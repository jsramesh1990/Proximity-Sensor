// server.cpp
#include <iostream>
#include <string>
#include <thread>
#include <vector>
#include <unordered_map>
#include <chrono>
#include <sstream>
#include <iomanip>
#include <ctime>
#include <fstream>

// Networking libraries
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <netdb.h>

// JSON library (install nlohmann/json with: sudo apt-get install nlohmann-json3-dev)
#include <nlohmann/json.hpp>
using json = nlohmann::json;

// WebSocket support (Simple-WebSocket-Server - single header)
#include "simple-websocket-server/server_ws.hpp"
using WsServer = SimpleWeb::SocketServer<SimpleWeb::WS>;

class ProximityServer {
private:
    int server_fd;
    struct sockaddr_in address;
    int port = 5000;
    std::unordered_map<std::string, json> sensor_data;
    std::mutex data_mutex;
    WsServer ws_server;
    std::thread ws_thread;
    std::ofstream db_file;

public:
    ProximityServer() {
        // Initialize database file
        db_file.open("sensor_data.csv", std::ios::app);
        if (!db_file) {
            std::cerr << "Failed to open database file" << std::endl;
        } else {
            // Write header if file is empty
            db_file.seekp(0, std::ios::end);
            if (db_file.tellp() == 0) {
                db_file << "timestamp,sensor_id,distance,status\n";
            }
        }
        
        // Initialize WebSocket server
        ws_server.config.port = 8080;
        
        // WebSocket endpoint
        auto& ws_endpoint = ws_server.endpoint["^/sensors/?$"];
        
        ws_endpoint.on_message = [this](std::shared_ptr<WsServer::Connection> connection, 
                                         std::shared_ptr<WsServer::Message> message) {
            auto message_str = message->string();
            // Broadcast sensor data to all connected clients
            broadcastSensorData();
        };
        
        ws_endpoint.on_open = [this](std::shared_ptr<WsServer::Connection> connection) {
            std::cout << "WebSocket client connected" << std::endl;
            // Send current sensor data to new client
            broadcastSensorData();
        };
        
        // Start WebSocket server in separate thread
        ws_thread = std::thread([this]() {
            std::cout << "WebSocket server starting on port 8080" << std::endl;
            ws_server.start();
        });
    }

    ~ProximityServer() {
        if (db_file.is_open()) {
            db_file.close();
        }
        ws_server.stop();
        if (ws_thread.joinable()) {
            ws_thread.join();
        }
    }

    std::string getCurrentTimestamp() {
        auto now = std::chrono::system_clock::now();
        auto in_time_t = std::chrono::system_clock::to_time_t(now);
        
        std::stringstream ss;
        ss << std::put_time(std::localtime(&in_time_t), "%Y-%m-%d %H:%M:%S");
        return ss.str();
    }

    std::string calculateStatus(float distance) {
        if (distance < 10.0) return "CRITICAL";
        else if (distance < 30.0) return "WARNING";
        else if (distance < 50.0) return "CAUTION";
        else return "SAFE";
    }

    void storeInDatabase(const std::string& sensor_id, float distance, const std::string& status) {
        std::lock_guard<std::mutex> lock(data_mutex);
        if (db_file.is_open()) {
            db_file << getCurrentTimestamp() << ","
                   << sensor_id << ","
                   << distance << ","
                   << status << "\n";
            db_file.flush();
        }
    }

    void broadcastSensorData() {
        std::lock_guard<std::mutex> lock(data_mutex);
        json data;
        for (const auto& [sensor_id, sensor_info] : sensor_data) {
            data[sensor_id] = sensor_info;
        }
        
        std::string data_str = data.dump();
        
        // Broadcast to all WebSocket clients
        auto& ws_endpoint = ws_server.endpoint["^/sensors/?$"];
        for (auto& connection : ws_endpoint.get_connections()) {
            auto send_stream = std::make_shared<WsServer::SendStream>();
            *send_stream << data_str;
            ws_endpoint.send(connection, send_stream);
        }
    }

    void handleClient(int client_socket) {
        char buffer[1024] = {0};
        std::string sensor_id = "unknown";
        
        while (true) {
            memset(buffer, 0, sizeof(buffer));
            int valread = read(client_socket, buffer, 1024);
            
            if (valread <= 0) {
                std::cout << "Client disconnected or error" << std::endl;
                break;
            }
            
            try {
                json data = json::parse(buffer);
                
                if (data.contains("sensor_id") && data.contains("distance")) {
                    sensor_id = data["sensor_id"];
                    float distance = data["distance"];
                    std::string status = calculateStatus(distance);
                    std::string timestamp = getCurrentTimestamp();
                    
                    // Store data
                    {
                        std::lock_guard<std::mutex> lock(data_mutex);
                        sensor_data[sensor_id] = {
                            {"distance", distance},
                            {"status", status},
                            {"timestamp", timestamp},
                            {"address", ""}  // Could get from socket if needed
                        };
                    }
                    
                    // Store in database
                    storeInDatabase(sensor_id, distance, status);
                    
                    // Broadcast update
                    broadcastSensorData();
                    
                    std::cout << "[" << sensor_id << "] Distance: " 
                              << distance << "cm - Status: " << status << std::endl;
                    
                    // Send acknowledgment
                    std::string ack = "ACK";
                    send(client_socket, ack.c_str(), ack.length(), 0);
                }
            } catch (const std::exception& e) {
                std::cerr << "JSON parse error: " << e.what() << std::endl;
            }
        }
        
        close(client_socket);
    }

    void start() {
        // Create TCP socket
        if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
            perror("Socket failed");
            exit(EXIT_FAILURE);
        }
        
        // Set socket options
        int opt = 1;
        if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, 
                       &opt, sizeof(opt))) {
            perror("setsockopt failed");
            exit(EXIT_FAILURE);
        }
        
        address.sin_family = AF_INET;
        address.sin_addr.s_addr = INADDR_ANY;
        address.sin_port = htons(port);
        
        // Bind socket
        if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
            perror("Bind failed");
            exit(EXIT_FAILURE);
        }
        
        // Listen for connections
        if (listen(server_fd, 3) < 0) {
            perror("Listen failed");
            exit(EXIT_FAILURE);
        }
        
        std::cout << "TCP Server listening on port " << port << std::endl;
        
        // Accept connections
        while (true) {
            int addrlen = sizeof(address);
            int client_socket = accept(server_fd, (struct sockaddr *)&address, 
                                      (socklen_t*)&addrlen);
            
            if (client_socket < 0) {
                perror("Accept failed");
                continue;
            }
            
            std::cout << "New client connected" << std::endl;
            
            // Handle client in separate thread
            std::thread client_thread(&ProximityServer::handleClient, this, client_socket);
            client_thread.detach();
        }
    }
};

int main() {
    ProximityServer server;
    server.start();
    return 0;
}
