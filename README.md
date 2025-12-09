# Proximity Sensor Monitoring System

A mixed-language, server-client architecture proximity sensor monitoring system with real-time visualization dashboard.

##  Project Overview

This project implements a complete IoT-style proximity monitoring system using three different programming languages, each optimized for its specific role:

- **C++ Server** - High-performance TCP/WebSocket server
- **C Client** - Efficient, low-level sensor interface
- **Python Dashboard** - Rich GUI with real-time visualization

##  Features

- **Real-time Monitoring**: Live distance readings from multiple sensors
- **Multi-language Architecture**: Optimized performance for each component
- **WebSocket Support**: Real-time bidirectional communication
- **Historical Data**: CSV-based data logging and retrieval
- **Alert System**: Visual status indicators (SAFE, CAUTION, WARNING, CRITICAL)
- **Cross-platform**: Runs on Linux, with Docker support
- **Modular Design**: Each component can be modified independently

##  System Architecture

```
<img width="629" height="201" alt="flow" src="https://github.com/user-attachments/assets/51183aac-b191-409c-922d-5b3aa264eade" />



┌─────────────────┐    TCP/JSON    ┌─────────────────┐    WebSocket    ┌─────────────────┐
│                 ├────────────────►│                 ├────────────────►│                 │
│   C Client      │                │   C++ Server    │                 │   Python        │
│  (Sensor Node)  │                │   (Middleware)  │                 │   Dashboard     │
│                 │◄───────────────┤                 │◄────────────────┤                 │
└─────────────────┘    ACK         └─────────────────┘    Broadcast    └─────────────────┘
```

### Workflow

1. **Sensor Data Collection** (C Client)
   ```
   Sensor Reading → JSON Serialization → TCP Transmission
   ```

2. **Server Processing** (C++ Server)
   ```
   TCP Reception → Data Parsing → Status Calculation → 
   Database Storage → WebSocket Broadcast
   ```

3. **Visualization** (Python Dashboard)
   ```
   WebSocket Reception → Data Processing → GUI Update → 
   Chart Visualization → User Interaction
   ```

##  Technology Stack

| Component | Language | Purpose | Key Libraries |
|-----------|----------|---------|---------------|
| Server | C++17 | Data processing & distribution | OpenSSL, Simple-WebSocket-Server |
| Client | C11 | Sensor interface & communication | Jansson (JSON), pthreads |
| Dashboard | Python 3.9 | User interface & visualization | Tkinter, matplotlib, websocket-client |

##  Project Structure

```
proximity-system/
├── server.cpp              # C++ TCP/WebSocket server
├── sensor_client.c         # C sensor client
├── dashboard.py            # Python GUI dashboard
├── Makefile               # Build automation
├── run-project.sh         # One-step execution script
├── docker-compose.yml     # Container orchestration
├── requirements.txt       # Python dependencies
├── config.json           # System configuration
├── README.md            # This file
├── logs/                # Runtime logs
├── data/               # Data storage
└── simple-websocket-server/
    └── server_ws.hpp    # WebSocket library
```

### Prerequisites

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install gcc g++ python3 libjansson-dev \
     nlohmann-json3-dev libssl-dev python3-pip wget
```

### One-Step Execution (Recommended)

```bash
# Make the script executable
chmod +x run-project.sh

# Build and run everything
./run-project.sh
```

### Alternative Methods

**Using Makefile:**
```bash
# Build all components
make all

# Run everything
make run-all

# Check system status
make status

# Stop the system
make stop
```

**Using Docker:**
```bash
# Build and run with Docker
docker-compose up --build

# Run in background
docker-compose up -d
```

##  Manual Setup

### 1. Compile C++ Server
```bash
g++ -std=c++17 -o proximity_server server.cpp -lpthread -lssl -lcrypto
```

### 2. Compile C Client
```bash
gcc -o sensor_client sensor_client.c -lpthread -ljansson -lm
```

### 3. Install Python Dependencies
```bash
pip3 install websocket-client pandas matplotlib
```

### 4. Run Components

**Terminal 1 - Server:**
```bash
./proximity_server
```

**Terminal 2 - Client:**
```bash
./sensor_client
```

**Terminal 3 - Dashboard:**
```bash
python3 dashboard.py
```

##  Communication Protocols

### TCP Protocol (Client → Server)
```json
{
  "sensor_id": "sensor_01",
  "distance": 45.5,
  "timestamp": "2024-01-15 14:30:25"
}
```

### WebSocket Protocol (Server → Dashboard)
```json
{
  "sensor_01": {
    "distance": 45.5,
    "status": "SAFE",
    "timestamp": "2024-01-15 14:30:25"
  },
  "sensor_02": {
    "distance": 15.2,
    "status": "WARNING",
    "timestamp": "2024-01-15 14:30:26"
  }
}
```

##  Dashboard Features

1. **Real-time Sensor Grid**
   - Visual status indicators with color coding
   - Live distance readings
   - Progress bars showing proximity levels
   - Last update timestamps

2. **Historical Charts**
   - Time-series distance plots
   - Multi-sensor overlay comparison
   - Configurable time window

3. **Control Panel**
   - Connection management
   - Data export to CSV
   - System configuration

4. **Event Logging**
   - Real-time system events
   - Connection status
   - Error reporting

##  Sensor Integration

### Simulated Sensors
The system includes simulated sensors that generate realistic distance data with noise and object movement patterns.

### Real Hardware Integration
Uncomment the hardware section in `sensor_client.c` and connect:

```c
// Example for HC-SR04 Ultrasonic Sensor
TRIG_PIN = 23;  // GPIO23
ECHO_PIN = 24;  // GPIO24
```

### Custom Sensor Support
To add custom sensors:

1. Modify the `read_sensor_distance()` function
2. Implement your sensor's communication protocol
3. Update the JSON data format if needed

##  Configuration

Edit `config.json` to customize:

```json
{
  "server": {
    "tcp_port": 5000,
    "websocket_port": 8080,
    "max_clients": 10
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
```

##  Data Flow Details

### Step-by-Step Process

1. **Initialization**
   ```
   Server starts → Creates TCP socket (port 5000) → 
   Creates WebSocket server (port 8080) → Initializes database
   ```

2. **Sensor Connection**
   ```
   Client connects to server → Authentication (optional) → 
   Receives ACK → Enters data transmission loop
   ```

3. **Data Transmission**
   ```
   Read sensor → Create JSON → TCP send → Server receives → 
   Parse JSON → Calculate status → Store in DB → 
   WebSocket broadcast → Dashboard updates
   ```

4. **User Interaction**
   ```
   Dashboard connects via WebSocket → Receives updates → 
   Updates GUI → User interacts → Sends commands (optional)
   ```

### Error Handling

- **Connection Loss**: Automatic reconnection attempts
- **Data Corruption**: JSON validation and ACK mechanism
- **Server Failure**: Graceful client shutdown
- **Dashboard Crash**: WebSocket reconnection with data sync

##  Docker Deployment

### Build Images
```bash
docker build -f Dockerfile.server -t proximity-server .
docker build -f Dockerfile.client -t sensor-client .
docker build -f Dockerfile.dashboard -t dashboard .
```

### Or use Docker Compose
```bash
docker-compose build
docker-compose up
```

##  Testing

### Test Sensor Simulation
```bash
# Run with 5 sensors at 1-second intervals
./sensor_client --count 5 --interval 1
```

### Test Server Only
```bash
# Start server
./proximity_server

# Test connection with netcat
echo '{"sensor_id":"test","distance":25.5}' | nc localhost 5000
```

### Test WebSocket
```bash
# Using wscat
npm install -g wscat
wscat -c ws://localhost:8080/sensors
```

##  Performance Metrics

- **Latency**: < 100ms end-to-end
- **Throughput**: Supports 100+ sensors
- **Memory**: ~50MB total system usage
- **CPU**: < 5% per component (idle)

##  Troubleshooting

### Common Issues

1. **Compilation Errors**
   ```bash
   # Missing libraries
   sudo apt-get install libjansson-dev nlohmann-json3-dev libssl-dev
   ```

2. **Connection Issues**
   ```bash
   # Check if ports are in use
   sudo netstat -tulpn | grep -E '5000|8080'
   
   # Check firewall
   sudo ufw allow 5000/tcp
   sudo ufw allow 8080/tcp
   ```

3. **Dashboard Not Opening**
   ```bash
   # Check Python dependencies
   pip3 install --upgrade websocket-client pandas matplotlib
   
   # Check logs
   tail -f logs/dashboard.log
   ```

### Debug Mode
```bash
# Run with verbose logging
./proximity_server --debug 2>&1 | tee debug.log
```

##  Logging

Logs are stored in the `logs/` directory:
- `server.log` - C++ server logs
- `client.log` - C client logs
- `dashboard.log` - Python application logs
- `sensor_data.csv` - Historical sensor data

##  API Endpoints

### TCP Endpoint
- `localhost:5000` - Sensor data ingestion

### WebSocket Endpoints
- `ws://localhost:8080/sensors` - Real-time sensor data

### HTTP Endpoints (Future)
- `GET /api/sensors` - List all sensors
- `GET /api/history/:id` - Historical data
- `POST /api/alert` - Configure alerts

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

##  License

MIT License - See LICENSE file for details

##  Acknowledgments

- [Simple-WebSocket-Server](https://github.com/eidheim/Simple-WebSocket-Server) for C++ WebSocket implementation
- [Jansson](https://github.com/akheron/jansson) for C JSON library
- [nlohmann/json](https://github.com/nlohmann/json) for C++ JSON library

---

**Happy Monitoring!** 
