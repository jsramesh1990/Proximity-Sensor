# **Complete Workflow Documentation**

## **📖 Project Workflow in Detail**

### **1. Overall System Flow**

The proximity sensor monitoring system follows a **three-tier architecture** where each component handles specific responsibilities:

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   TIER 1    │   │   TIER 2    │   │   TIER 3    │
│  Data       │   │  Processing │   │  Presentation│
│  Acquisition│   │  & Storage  │   │  & Control  │
│             │   │             │   │             │
│  C Client   │──▶│  C++ Server │──▶│  Python     │
│  (Sensors)  │   │  (Middleware)│   │  Dashboard  │
└─────────────┘   └─────────────┘   └─────────────┘
      │                  │                  │
  Physical        Data Processing    User Interaction
  Hardware            Logic           & Visualization
```

### **2. Step-by-Step Operational Workflow**

#### **Phase 1: System Initialization**

```
Step 1.1: Server Boot
├── C++ server starts and initializes:
│   ├── Creates TCP socket on port 5000
│   ├── Creates WebSocket server on port 8080
│   ├── Initializes SQLite database/CSV file
│   ├── Loads configuration from config.json
│   └── Starts listening for connections

Step 1.2: Client Initialization
├── C client program starts:
│   ├── Reads sensor configuration
│   ├── Initializes GPIO pins (for real hardware)
│   ├── Establishes connection with server
│   └── Enters main sensing loop

Step 1.3: Dashboard Launch
├── Python dashboard starts:
│   ├── Loads GUI components (Tkinter)
│   ├── Connects to WebSocket server (port 8080)
│   ├── Loads historical data from CSV
│   └── Displays real-time interface
```

#### **Phase 2: Continuous Data Flow**

```
Step 2.1: Sensor Reading (Every 2 seconds)
├── C Client (sensor_client.c):
│   ├── Calls read_sensor_distance():
│   │   ├── (Simulated) Generates random distance 0-100cm
│   │   ├── (Real) Triggers ultrasonic sensor & measures echo
│   │   └── Applies noise and object movement simulation
│   ├── Creates JSON payload:
│   │   {
│   │     "sensor_id": "sensor_01",
│   │     "distance": 45.5,
│   │     "timestamp": "2024-01-15 14:30:25"
│   │   }
│   └── Sends via TCP to server:5000

Step 2.2: Server Processing
├── C++ Server (server.cpp):
│   ├── TCP Receiver thread accepts data
│   ├── Parses JSON using nlohmann/json library
│   ├── Calculates status based on thresholds:
│   │   ├── < 10cm → CRITICAL (Red/Purple)
│   │   ├── 10-30cm → WARNING (Orange)
│   │   ├── 30-50cm → CAUTION (Yellow)
│   │   └── > 50cm → SAFE (Green)
│   ├── Stores in CSV database:
│   │   timestamp,sensor_id,distance,status
│   └── Broadcasts via WebSocket to all connected dashboards

Step 2.3: Dashboard Update
├── Python Dashboard (dashboard.py):
│   ├── WebSocket client receives JSON data
│   ├── Updates sensor widgets in real-time:
│   │   ├── Distance display with colored text
│   │   ├── Progress bar showing proximity level
│   │   ├── Status indicator with color coding
│   │   └── Last update timestamp
│   ├── Updates historical chart:
│   │   ├── Adds new data point to time-series
│   │   ├── Maintains last 50 readings per sensor
│   │   └── Animates chart with smooth transitions
│   └── Logs events to text window
```

#### **Phase 3: User Interaction Flow**

```
Step 3.1: Monitoring
├── User observes:
│   ├── Real-time distance readings from multiple sensors
│   ├── Color-coded status alerts
│   ├── Historical trends on chart
│   └── Event log for system activities

Step 3.2: Control Actions
├── User can:
│   ├── Export data to CSV with timestamp
│   ├── Adjust chart history length
│   ├── Change WebSocket server address
│   └── Refresh connections manually

Step 3.3: Alert Response
├── System triggers:
│   ├── Visual alerts on dashboard
│   ├── Color changes (Green→Yellow→Red→Purple)
│   ├── Progress bar updates
│   └── Log entries for critical events
```

#### **Phase 4: Error Handling & Recovery**

```
Step 4.1: Connection Issues
├── If client loses connection:
│   ├── Attempts automatic reconnection every 5 seconds
│   ├── Buffers sensor readings locally (future enhancement)
│   └── Logs connection attempts

Step 4.2: Data Corruption
├── If invalid data received:
│   ├── Server sends NACK (negative acknowledgment)
│   ├── Client retransmits after delay
│   └── Error logged to server.log

Step 4.3: Dashboard Disconnect
├── If dashboard loses WebSocket connection:
│   ├── Shows "Disconnected" status
│   ├── Attempts auto-reconnect
│   └── Resumes normal operation on reconnection
```

### **3. Docker Implementation Workflow**

#### **Why Docker for This Project?**

Docker provides:
1. **Isolation** - Each component runs in its own container
2. **Portability** - Runs consistently across different systems
3. **Easy Deployment** - One command to start entire system
4. **Resource Management** - Controlled CPU/Memory allocation
5. **Network Isolation** - Secure internal communication

#### **Docker Architecture**

```
┌─────────────────────────────────────────────────┐
│              Docker Host System                 │
│                                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐│
│  │            │  │            │  │            ││
│  │   C++      │  │   C        │  │   Python   ││
│  │  Server    │  │  Client    │  │  Dashboard ││
│  │  Container │  │  Container │  │  Container ││
│  │            │  │            │  │            ││
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘│
│        │                │                │      │
│        └────────────────┼────────────────┘      │
│                         │                       │
│                 ┌───────┴───────┐               │
│                 │  Docker       │               │
│                 │  Network      │               │
│                 │  (proximity-net)              │
│                 └───────────────┘               │
└─────────────────────────────────────────────────┘
```

#### **Docker Workflow Steps**

##### **Step 1: Build Docker Images**

```bash
# Build all three images from Dockerfiles
docker-compose build

# This executes:
# 1. Builds C++ server image (FROM gcc:11)
# 2. Builds C client image (FROM gcc:11)
# 3. Builds Python dashboard image (FROM python:3.9-slim)
```

##### **Step 2: Container Network Setup**

```yaml
# docker-compose.yml creates:
# - Internal Docker network 'proximity-net'
# - Port mappings:
#   Server: 5000 (TCP) and 8080 (WebSocket) exposed
#   Dashboard: 8081 (GUI) exposed
#   Client: No ports exposed (internal only)
```

##### **Step 3: Container Startup Sequence**

```
Time 0s: Docker Compose starts network
Time 1s: Server container starts (depends on nothing)
├── Runs ./proximity_server
├── Opens ports 5000 and 8080
├── Waits for connections
└── Logs: "Server listening on 0.0.0.0:5000"

Time 5s: Client container starts (depends_on: server)
├── Runs sensor_client
├── Connects to server:5000
├── Starts sensor simulation
└── Logs: "Sensor sensor_01 started"

Time 7s: Dashboard container starts (depends_on: server)
├── Runs python dashboard.py
├── Connects to ws://server:8080/sensors
├── Launches Tkinter GUI
└── Logs: "Dashboard started successfully"
```

##### **Step 4: Inter-Container Communication**

```
# Inside Docker network:
Client → Server: Uses internal DNS 'proximity-server:5000'
Dashboard → Server: Uses 'ws://proximity-server:8080/sensors'

# External access (from host machine):
Web browser: http://localhost:8081 (if web dashboard)
TCP test: nc localhost 5000
WebSocket test: wscat -c ws://localhost:8080/sensors
```

##### **Step 5: Data Persistence**

```yaml
# Volumes configuration:
volumes:
  - ./data:/app/data    # Shared CSV database
  - ./logs:/app/logs    # Shared log files
  
# Each container sees the same /app/data directory
# Data persists even after containers are stopped
```

##### **Step 6: Monitoring & Management**

```bash
# View all running containers
docker-compose ps

# View logs (all containers)
docker-compose logs -f

# View specific container logs
docker-compose logs -f proximity-server

# Access container shell
docker-compose exec proximity-server /bin/bash

# Check resource usage
docker stats

# Scale sensor clients (if needed)
docker-compose up --scale sensor-client=5
```

#### **Docker Development Workflow**

##### **For Development:**

```bash
# 1. Start with bind mounts for live code updates
docker-compose -f docker-compose.dev.yml up

# 2. This mounts local source code into containers:
#    - ./server.cpp → /app/server.cpp
#    - ./sensor_client.c → /app/sensor_client.c
#    - ./dashboard.py → /app/dashboard.py

# 3. Changes to local files instantly reflect in containers
# 4. Use volume for dependencies to avoid re-downloading
```

##### **For Production:**

```bash
# 1. Build optimized images
docker-compose -f docker-compose.prod.yml build

# 2. Push to container registry
docker-compose push

# 3. Deploy to production server
docker-compose -f docker-compose.prod.yml up -d

# 4. Set up monitoring
docker-compose logs --tail=100 -f
```

#### **Dockerfile Breakdown**

##### **C++ Server Dockerfile Strategy:**

```dockerfile
# Multi-stage build:
# Stage 1: Builder (includes compilers and build tools)
FROM gcc:11 as builder
# Install build dependencies
# Compile server binary

# Stage 2: Runtime (minimal base image)
FROM ubuntu:22.04
# Copy only compiled binary
# Install runtime dependencies only
# Result: Small, secure image
```

##### **C Client Dockerfile Strategy:**

```dockerfile
# Single-stage build (simpler)
FROM gcc:11
# Install dependencies
# Compile binary
# Set entrypoint script for configuration
```

##### **Python Dashboard Dockerfile Strategy:**

```dockerfile
# Optimized Python image
FROM python:3.9-slim
# Install system dependencies for GUI
# Copy requirements.txt first (caching optimization)
# Install Python packages
# Copy application code
```

#### **Docker Compose Configuration Details**

```yaml
services:
  proximity-server:
    build:
      context: .  # Uses current directory
      dockerfile: Dockerfile.server
    container_name: proximity-server
    ports:
      - "5000:5000"  # Host:Container port mapping
      - "8080:8080"
    volumes:
      - ./data:/app/data  # Bind mount for data persistence
      - ./logs:/app/logs
    networks:
      - proximity-net  # Custom network for isolation
    environment:
      - LOG_LEVEL=INFO  # Environment variables
    restart: unless-stopped  # Auto-restart on failure
    healthcheck:  # Container health monitoring
      test: ["CMD", "nc", "-z", "localhost", "5000"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### **Advanced Docker Features Used**

##### **1. Health Checks:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

##### **2. Resource Limits:**
```yaml
deploy:
  resources:
    limits:
      cpus: '0.50'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

##### **3. Secrets Management:**
```yaml
secrets:
  db_password:
    file: ./secrets/db_password.txt
```

##### **4. Logging Configuration:**
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

#### **Docker Deployment Scenarios**

##### **Scenario 1: Local Development**
```bash
# Using development compose file with hot reload
docker-compose -f docker-compose.dev.yml up

# Features:
# - Source code mounted for live editing
# - Debug tools included
# - Volume for dependency caching
```

##### **Scenario 2: Testing/CI**
```bash
# Using test compose file
docker-compose -f docker-compose.test.yml up

# Features:
# - Test data pre-loaded
# - Mock sensors for testing
# - Automated test execution
```

##### **Scenario 3: Production Deployment**
```bash
# Using production compose file
docker-compose -f docker-compose.prod.yml up -d

# Features:
# - Optimized images
# - Resource limits
# - Health checks
# - Log aggregation
# - Backup volumes
```

#### **Docker Commands Cheat Sheet**

```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Execute command in container
docker-compose exec proximity-server ls -la

# Scale services
docker-compose up --scale sensor-client=3

# View resource usage
docker-compose top

# Copy files from container
docker cp proximity-server:/app/logs/server.log ./local/

# Backup volumes
docker run --rm -v proximity-system_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/backup.tar.gz /data
```

#### **Docker Security Best Practices Applied**

1. **Non-root users** in containers
2. **Read-only root filesystem** where possible
3. **Resource limits** to prevent DoS
4. **Network segmentation** with custom networks
5. **Secret management** for credentials
6. **Regular updates** of base images
7. **Image scanning** for vulnerabilities

### **4. Real-World Deployment Scenarios**

#### **Scenario A: Single Board Computer (Raspberry Pi)**
```
Physical Setup:
├── Raspberry Pi 4 (4GB RAM)
├── HC-SR04 Ultrasonic Sensors (connected via GPIO)
├── Running all three components natively
└── Local display for dashboard

Docker Advantage:
├── Easy updates without breaking dependencies
├── Isolated sensor access
└── Backup/restore capability
```

#### **Scenario B: Industrial Monitoring**
```
Physical Setup:
├── Multiple sensor nodes (C clients) across factory
├── Central server in control room
├── Multiple dashboard stations
└── Historical data analysis server

Docker Advantage:
├── Scalable with container orchestration (Kubernetes)
├── Centralized logging with ELK stack
├── High availability with container replication
└── Rolling updates without downtime
```

#### **Scenario C: Cloud Deployment**
```
Physical Setup:
├── Sensors with cellular/WiFi connectivity
├── Cloud server (AWS/Azure/Google Cloud)
├── Web-based dashboard accessible globally
└── Mobile app for alerts

Docker Advantage:
├── Container registry for easy deployment
├── Auto-scaling based on sensor count
├── Cloud-native monitoring integration
└── Cost optimization with resource limits
```

### **5. Performance Optimization**

#### **Memory Optimization:**
```c
// C Client: Efficient memory usage
- Stack allocation for sensor data
- Reusable JSON buffers
- Minimal library dependencies

// C++ Server: Connection pooling
- Thread pool for client handling
- Memory pool for JSON objects
- Connection reuse

// Python Dashboard: Lazy loading
- Chart updates only when data changes
- Widget creation on-demand
- Garbage collection optimization
```

#### **Network Optimization:**
```
1. TCP Nagle's algorithm disabled for low latency
2. WebSocket compression enabled
3. Binary protocol option for high-frequency sensors
4. Connection keep-alive to reduce handshake overhead
```

### **6. Extension Points**

#### **Future Enhancements:**

1. **MQTT Support** - Add MQTT broker for IoT integration
2. **Database Backend** - Replace CSV with PostgreSQL/InfluxDB
3. **Mobile App** - React Native app for mobile monitoring
4. **Alert System** - Email/SMS notifications for critical events
5. **Machine Learning** - Predictive maintenance using historical data
6. **Edge Computing** - Local processing on sensor nodes
7. **Blockchain** - Immutable audit trail for sensor data

### **7. Maintenance Workflow**

#### **Daily Operations:**
```
1. Check system status: make status
2. Review logs: tail -f logs/server.log
3. Backup data: ./scripts/backup.sh
4. Monitor resource usage: docker stats
5. Check for updates: ./scripts/update-check.sh
```

#### **Weekly Operations:**
```
1. Rotate logs: logrotate configuration
2. Clean old data: ./scripts/cleanup.sh
3. Update containers: docker-compose pull
4. Security scan: trivy image proximity-server
5. Performance review: analyze logs/performance.log
```

### **8. Troubleshooting Flowchart**

```
Start: Issue detected
  │
  ▼
Is server running? → No → Start server: ./proximity_server
  │ Yes
  ▼
Can client connect? → No → Check network/firewall
  │ Yes
  ▼
Is data being received? → No → Check sensor hardware
  │ Yes
  ▼
Is dashboard showing data? → No → Check WebSocket connection
  │ Yes
  ▼
System operational ✓
```

This comprehensive workflow ensures that the proximity sensor monitoring system operates reliably, efficiently, and can be easily deployed and maintained using modern containerization techniques.
