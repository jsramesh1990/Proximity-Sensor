#!/bin/bash
# run-project.sh - One-step build and run script

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${GREEN}"
    echo "=========================================="
    echo "  Proximity Sensor System"
    echo "  Mixed Language Project"
    echo "=========================================="
    echo -e "${NC}"
}

print_step() {
    echo -e "${YELLOW}[STEP] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

check_dependencies() {
    print_step "Checking dependencies..."
    
    local missing_deps=()
    
    # Check for C/C++ compilers
    if ! command -v gcc &> /dev/null; then
        missing_deps+=("gcc")
    fi
    
    if ! command -v g++ &> /dev/null; then
        missing_deps+=("g++")
    fi
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Check for libraries
    if ! dpkg -l | grep -q libjansson-dev; then
        missing_deps+=("libjansson-dev")
    fi
    
    if ! dpkg -l | grep -q nlohmann-json3-dev; then
        missing_deps+=("nlohmann-json3-dev")
    fi
    
    if ! dpkg -l | grep -q libssl-dev; then
        missing_deps+=("libssl-dev")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_step "Installing missing dependencies..."
        sudo apt-get update
        sudo apt-get install -y "${missing_deps[@]}"
    fi
    
    print_success "Dependencies satisfied"
}

download_websocket_header() {
    print_step "Downloading WebSocket header..."
    
    mkdir -p simple-websocket-server
    if [ ! -f "simple-websocket-server/server_ws.hpp" ]; then
        wget -q https://raw.githubusercontent.com/eidheim/Simple-WebSocket-Server/master/ws_server_ws.hpp \
             -O simple-websocket-server/server_ws.hpp
    fi
    
    print_success "WebSocket header downloaded"
}

setup_directories() {
    print_step "Setting up directories..."
    
    mkdir -p logs data
    
    print_success "Directories created"
}

create_config() {
    print_step "Creating configuration file..."
    
    if [ ! -f "config.json" ]; then
        cat > config.json << EOF
{
  "server": {
    "tcp_port": 5000,
    "websocket_port": 8080,
    "max_clients": 10,
    "log_file": "logs/server.log"
  },
  "sensors": {
    "update_interval": 2,
    "distance_thresholds": {
      "critical": 10,
      "warning": 30,
      "caution": 50
    }
  }
}
EOF
    fi
    
    print_success "Configuration file created"
}

compile_server() {
    print_step "Compiling C++ server..."
    
    g++ -std=c++17 -o proximity_server server.cpp -lpthread -lssl -lcrypto
    
    if [ $? -eq 0 ]; then
        print_success "Server compiled successfully"
    else
        print_error "Failed to compile server"
        exit 1
    fi
}

compile_client() {
    print_step "Compiling C client..."
    
    gcc -o sensor_client sensor_client.c -lpthread -ljansson -lm
    
    if [ $? -eq 0 ]; then
        print_success "Client compiled successfully"
    else
        print_error "Failed to compile client"
        exit 1
    fi
}

install_python_deps() {
    print_step "Installing Python dependencies..."
    
    python3 -m pip install --upgrade pip > /dev/null 2>&1
    python3 -m pip install websocket-client pandas matplotlib > /dev/null 2>&1
    
    print_success "Python dependencies installed"
}

start_server() {
    print_step "Starting C++ server..."
    
    ./proximity_server > logs/server.log 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > pids.txt
    
    # Wait for server to start
    sleep 3
    
    if kill -0 $SERVER_PID 2>/dev/null; then
        print_success "Server started (PID: $SERVER_PID)"
    else
        print_error "Server failed to start"
        exit 1
    fi
}

start_client() {
    print_step "Starting sensor client..."
    
    ./sensor_client > logs/client.log 2>&1 &
    CLIENT_PID=$!
    echo $CLIENT_PID >> pids.txt
    
    sleep 1
    
    if kill -0 $CLIENT_PID 2>/dev/null; then
        print_success "Client started (PID: $CLIENT_PID)"
    else
        print_error "Client failed to start"
        exit 1
    fi
}

start_dashboard() {
    print_step "Starting Python dashboard..."
    
    python3 dashboard.py > logs/dashboard.log 2>&1 &
    DASH_PID=$!
    echo $DASH_PID >> pids.txt
    
    sleep 2
    
    if kill -0 $DASH_PID 2>/dev/null; then
        print_success "Dashboard started (PID: $DASH_PID)"
        echo ""
        echo -e "${GREEN}Dashboard should open automatically.${NC}"
        echo -e "${YELLOW}If not, check logs/dashboard.log${NC}"
    else
        print_error "Dashboard failed to start"
        exit 1
    fi
}

show_status() {
    echo ""
    echo -e "${GREEN}=========================================="
    echo "  System Status"
    echo "=========================================="
    echo -e "${NC}"
    
    echo "Server:      $(if kill -0 $SERVER_PID 2>/dev/null; then echo -e "${GREEN}Running${NC}"; else echo -e "${RED}Stopped${NC}"; fi)"
    echo "Client:      $(if kill -0 $CLIENT_PID 2>/dev/null; then echo -e "${GREEN}Running${NC}"; else echo -e "${RED}Stopped${NC}"; fi)"
    echo "Dashboard:   $(if kill -0 $DASH_PID 2>/dev/null; then echo -e "${GREEN}Running${NC}"; else echo -e "${RED}Stopped${NC}"; fi)"
    
    echo ""
    echo -e "${YELLOW}Logs are available in:${NC}"
    echo "  Server:    logs/server.log"
    echo "  Client:    logs/client.log"
    echo "  Dashboard: logs/dashboard.log"
    echo ""
    echo -e "${YELLOW}To stop all components, run:${NC}"
    echo "  ./run-project.sh stop"
    echo ""
}

stop_system() {
    print_step "Stopping all components..."
    
    if [ -f "pids.txt" ]; then
        while read pid; do
            if kill -0 $pid 2>/dev/null; then
                kill $pid 2>/dev/null
                echo "Stopped PID: $pid"
            fi
        done < pids.txt
        rm -f pids.txt
    fi
    
    # Cleanup any remaining processes
    pkill -f proximity_server 2>/dev/null || true
    pkill -f sensor_client 2>/dev/null || true
    pkill -f dashboard.py 2>/dev/null || true
    
    print_success "All components stopped"
}

cleanup() {
    print_step "Cleaning up..."
    
    rm -f proximity_server sensor_client
    rm -f pids.txt
    
    print_success "Cleanup complete"
}

# Main execution flow
case "$1" in
    "stop")
        stop_system
        exit 0
        ;;
    "clean")
        cleanup
        exit 0
        ;;
    "status")
        # Check if components are running
        echo "Checking system status..."
        # Implementation for status check
        exit 0
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no command)  Build and run entire system"
        echo "  stop          Stop all running components"
        echo "  clean         Clean build artifacts"
        echo "  status        Check system status"
        echo "  help          Show this help message"
        exit 0
        ;;
esac

# Main build and run process
print_header

# Check if we're in the right directory
if [ ! -f "server.cpp" ] || [ ! -f "sensor_client.c" ] || [ ! -f "dashboard.py" ]; then
    print_error "Required source files not found!"
    echo "Please run this script from the project directory containing:"
    echo "  server.cpp, sensor_client.c, dashboard.py"
    exit 1
fi

# Run all steps
check_dependencies
download_websocket_header
setup_directories
create_config
compile_server
compile_client
install_python_deps
start_server
start_client
start_dashboard
show_status

# Setup trap to cleanup on Ctrl+C
trap 'echo ""; print_step "Interrupt received, stopping..."; stop_system; exit 0' INT

echo ""
echo -e "${GREEN}System is running! Press Ctrl+C to stop.${NC}"
echo ""

# Keep script running
while true; do
    sleep 1
done
