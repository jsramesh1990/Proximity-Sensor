# Makefile
.PHONY: all clean server client python install run run-all stop help

# Configuration
CC = gcc
CXX = g++
PYTHON = python3
CFLAGS = -Wall -Wextra -O2
CXXFLAGS = -std=c++17 -Wall -Wextra -O2
LDFLAGS = 
SERVER_EXEC = proximity_server
CLIENT_EXEC = sensor_client
PYTHON_APP = dashboard.py
SERVER_SRC = server.cpp
CLIENT_SRC = sensor_client.c
WEBSOCKET_HEADER = simple-websocket-server/server_ws.hpp
CONFIG_FILE = config.json
LOG_DIR = logs
DATA_DIR = data
VENV_DIR = venv
PID_FILE = pids.txt

# Colors for terminal output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

# Default target
all: deps server client python-deps

# Install dependencies
deps: check-deps download-deps
	@echo "$(GREEN)Dependencies check complete!$(NC)"

check-deps:
	@echo "$(YELLOW)Checking system dependencies...$(NC)"
	@command -v $(CC) >/dev/null 2>&1 || { echo >&2 "$(RED)C compiler not found. Installing...$(NC)"; sudo apt-get install gcc; }
	@command -v $(CXX) >/dev/null 2>&1 || { echo >&2 "$(RED)C++ compiler not found. Installing...$(NC)"; sudo apt-get install g++; }
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo >&2 "$(RED)Python3 not found. Installing...$(NC)"; sudo apt-get install python3 python3-pip; }
	@dpkg -l | grep -q libjansson-dev || { echo >&2 "$(RED)Jansson library not found. Installing...$(NC)"; sudo apt-get install libjansson-dev; }
	@dpkg -l | grep -q nlohmann-json3-dev || { echo >&2 "$(RED)Nlohmann JSON library not found. Installing...$(NC)"; sudo apt-get install nlohmann-json3-dev; }
	@dpkg -l | grep -q libssl-dev || { echo >&2 "$(RED)OpenSSL library not found. Installing...$(NC)"; sudo apt-get install libssl-dev; }

download-deps: $(WEBSOCKET_HEADER)

$(WEBSOCKET_HEADER):
	@echo "$(YELLOW)Downloading WebSocket server header...$(NC)"
	@mkdir -p simple-websocket-server
	@wget -q https://raw.githubusercontent.com/eidheim/Simple-WebSocket-Server/master/ws_server_ws.hpp -O $(WEBSOCKET_HEADER) || \
	 { echo "$(RED)Failed to download WebSocket header$(NC)"; exit 1; }
	@echo "$(GREEN)WebSocket header downloaded successfully!$(NC)"

# Build server
server: $(SERVER_SRC) $(WEBSOCKET_HEADER)
	@echo "$(YELLOW)Compiling C++ server...$(NC)"
	@$(CXX) $(CXXFLAGS) $(SERVER_SRC) -o $(SERVER_EXEC) -lpthread -lssl -lcrypto
	@echo "$(GREEN)Server compiled successfully!$(NC)"

# Build client
client: $(CLIENT_SRC)
	@echo "$(YELLOW)Compiling C client...$(NC)"
	@$(CC) $(CFLAGS) $(CLIENT_SRC) -o $(CLIENT_EXEC) -lpthread -ljansson -lm
	@echo "$(GREEN)Client compiled successfully!$(NC)"

# Install Python dependencies
python-deps:
	@echo "$(YELLOW)Installing Python dependencies...$(NC)"
	@$(PYTHON) -m pip install --upgrade pip > /dev/null 2>&1
	@$(PYTHON) -m pip install websocket-client pandas matplotlib > /dev/null 2>&1 || \
	 { echo "$(RED)Failed to install Python dependencies$(NC)"; exit 1; }
	@echo "$(GREEN)Python dependencies installed successfully!$(NC)"

python-venv:
	@echo "$(YELLOW)Creating Python virtual environment...$(NC)"
	@$(PYTHON) -m venv $(VENV_DIR)
	@. $(VENV_DIR)/bin/activate && pip install websocket-client pandas matplotlib
	@echo "$(GREEN)Virtual environment created!$(NC)"
	@echo "To activate: source $(VENV_DIR)/bin/activate"

# Create necessary directories and config files
setup-dirs:
	@mkdir -p $(LOG_DIR) $(DATA_DIR)
	@echo "$(GREEN)Created necessary directories$(NC)"

setup-config:
	@if [ ! -f $(CONFIG_FILE) ]; then \
		echo "$(YELLOW)Creating configuration file...$(NC)"; \
		echo '{\n  "server": {\n    "tcp_port": 5000,\n    "websocket_port": 8080,\n    "max_clients": 10,\n    "log_file": "logs/server.log"\n  },\n  "sensors": {\n    "update_interval": 2,\n    "distance_thresholds": {\n      "critical": 10,\n      "warning": 30,\n      "caution": 50\n    }\n  }\n}' > $(CONFIG_FILE); \
		echo "$(GREEN)Configuration file created$(NC)"; \
	fi

# Run commands
run-server: server setup-dirs setup-config
	@echo "$(YELLOW)Starting server...$(NC)"
	@echo "Server PID: $$!" >> $(PID_FILE)
	@./$(SERVER_EXEC) 2>&1 | tee $(LOG_DIR)/server.log &

run-client: client
	@echo "$(YELLOW)Starting sensor client...$(NC)"
	@echo "Client PID: $$!" >> $(PID_FILE)
	@./$(CLIENT_EXEC) 2>&1 | tee $(LOG_DIR)/client.log &

run-python: python-deps
	@echo "$(YELLOW)Starting Python dashboard...$(NC)"
	@$(PYTHON) $(PYTHON_APP) 2>&1 | tee $(LOG_DIR)/dashboard.log &

# Run all components in separate terminals (requires xterm)
run-all-xterm: all setup-dirs setup-config
	@echo "$(YELLOW)Starting all components in separate terminals...$(NC)"
	@xterm -title "Proximity Server" -e "./$(SERVER_EXEC)" &
	@echo "Server PID: $$!" >> $(PID_FILE)
	@sleep 2
	@xterm -title "Sensor Client" -e "./$(CLIENT_EXEC)" &
	@echo "Client PID: $$!" >> $(PID_FILE)
	@sleep 2
	@xterm -title "Dashboard" -e "$(PYTHON) $(PYTHON_APP)" &
	@echo "Dashboard PID: $$!" >> $(PID_FILE)
	@echo "$(GREEN)All components started!$(NC)"

# Run all in background
run-all: all setup-dirs setup-config
	@echo "$(YELLOW)Starting all components in background...$(NC)"
	@./$(SERVER_EXEC) > $(LOG_DIR)/server.log 2>&1 &
	@echo "Server PID: $$!" >> $(PID_FILE)
	@sleep 3
	@./$(CLIENT_EXEC) > $(LOG_DIR)/client.log 2>&1 &
	@echo "Client PID: $$!" >> $(PID_FILE)
	@sleep 2
	@$(PYTHON) $(PYTHON_APP) > $(LOG_DIR)/dashboard.log 2>&1 &
	@echo "Dashboard PID: $$!" >> $(PID_FILE)
	@echo "$(GREEN)All components started!$(NC)"
	@echo "$(YELLOW)Check logs in $(LOG_DIR)/ directory$(NC)"

# Stop all running components
stop:
	@echo "$(YELLOW)Stopping all components...$(NC)"
	@if [ -f $(PID_FILE) ]; then \
		while read line; do \
			pid=$$(echo $$line | awk '{print $$3}'); \
			if kill -0 $$pid 2>/dev/null; then \
				kill $$pid && echo "Stopped PID $$pid"; \
			fi; \
		done < $(PID_FILE); \
		rm -f $(PID_FILE); \
	fi
	@pkill -f $(SERVER_EXEC) 2>/dev/null || true
	@pkill -f $(CLIENT_EXEC) 2>/dev/null || true
	@pkill -f $(PYTHON_APP) 2>/dev/null || true
	@echo "$(GREEN)All components stopped!$(NC)"

# Clean build artifacts
clean:
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	@rm -f $(SERVER_EXEC) $(CLIENT_EXEC)
	@rm -f *.o *.so *.a
	@rm -rf __pycache__
	@rm -f sensor_data.csv
	@echo "$(GREEN)Clean complete!$(NC)"

clean-all: clean
	@echo "$(YELLOW)Cleaning all generated files...$(NC)"
	@rm -rf $(LOG_DIR) $(DATA_DIR) $(VENV_DIR)
	@rm -f $(CONFIG_FILE) $(PID_FILE)
	@rm -f sensor_export_*.csv
	@echo "$(GREEN)Full clean complete!$(NC)"

# Display system status
status:
	@echo "$(YELLOW)=== Proximity Sensor System Status ===$(NC)"
	@echo "Server: $$(if pgrep -x $(SERVER_EXEC) >/dev/null; then echo "$(GREEN)Running$(NC)"; else echo "$(RED)Stopped$(NC)"; fi)"
	@echo "Client: $$(if pgrep -x $(CLIENT_EXEC) >/dev/null; then echo "$(GREEN)Running$(NC)"; else echo "$(RED)Stopped$(NC)"; fi)"
	@echo "Dashboard: $$(if pgrep -f $(PYTHON_APP) >/dev/null; then echo "$(GREEN)Running$(NC)"; else echo "$(RED)Stopped$(NC)"; fi)"
	@echo "$(YELLOW)=====================================$(NC)"

# Install as system service (requires root)
install-service:
	@echo "$(YELLOW)Installing as system service...$(NC)"
	@sudo cp systemd/proximity-sensor.service /etc/systemd/system/
	@sudo systemctl daemon-reload
	@sudo systemctl enable proximity-sensor.service
	@echo "$(GREEN)Service installed! Start with: sudo systemctl start proximity-sensor$(NC)"

# Help message
help:
	@echo "$(YELLOW)=== Proximity Sensor Build System ===$(NC)"
	@echo "Available targets:"
	@echo "  all              - Build everything (default)"
	@echo "  server           - Build only C++ server"
	@echo "  client           - Build only C client"
	@echo "  python-deps      - Install Python dependencies"
	@echo "  run-server       - Build and run server"
	@echo "  run-client       - Build and run client"
	@echo "  run-python       - Run Python dashboard"
	@echo "  run-all          - Build and run all components in background"
	@echo "  run-all-xterm    - Run in separate xterm windows"
	@echo "  stop             - Stop all running components"
	@echo "  status           - Check system status"
	@echo "  clean            - Remove build artifacts"
	@echo "  clean-all        - Remove all generated files"
	@echo "  install-service  - Install as system service"
	@echo "  help             - Show this help message"
	@echo "$(YELLOW)=====================================$(NC)"
