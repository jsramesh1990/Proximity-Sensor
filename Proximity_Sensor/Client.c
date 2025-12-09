// sensor_client.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <math.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <pthread.h>
#include <jansson.h>  // Install with: sudo apt-get install libjansson-dev

#define PORT 5000
#define BUFFER_SIZE 1024
#define MAX_SENSORS 10

typedef struct {
    char sensor_id[32];
    char server_ip[16];
    int port;
    int interval;
    int running;
} SensorConfig;

// Simulated sensor reading (replace with actual hardware reading)
float read_sensor_distance() {
    // Simulate distance between 0-100cm with some noise
    float base = (float)(rand() % 100);
    float noise = ((float)rand() / RAND_MAX) * 10.0 - 5.0;
    float distance = base + noise;
    
    // Simulate object movement occasionally
    if (rand() % 10 < 3) {
        distance = distance * ((float)rand() / RAND_MAX);
    }
    
    // Ensure distance is within bounds
    if (distance < 0) distance = 0;
    if (distance > 100) distance = 100;
    
    return distance;
}

// Actual hardware sensor reading function (example for HC-SR04)
/*
float read_ultrasonic_sensor(int trigger_pin, int echo_pin) {
    // GPIO initialization would go here
    // For Raspberry Pi, use wiringPi or similar library
    
    struct timeval start, stop;
    long travel_time;
    float distance;
    
    // Send trigger pulse
    digitalWrite(trigger_pin, LOW);
    usleep(2);
    digitalWrite(trigger_pin, HIGH);
    usleep(10);
    digitalWrite(trigger_pin, LOW);
    
    // Wait for echo start
    while (digitalRead(echo_pin) == LOW);
    gettimeofday(&start, NULL);
    
    // Wait for echo end
    while (digitalRead(echo_pin) == HIGH);
    gettimeofday(&stop, NULL);
    
    // Calculate distance
    travel_time = (stop.tv_sec - start.tv_sec) * 1000000 + 
                  (stop.tv_usec - start.tv_usec);
    distance = travel_time * 0.0343 / 2.0;  // Speed of sound in cm/µs
    
    return distance;
}
*/

char* get_timestamp() {
    static char buffer[64];
    time_t rawtime;
    struct tm *timeinfo;
    
    time(&rawtime);
    timeinfo = localtime(&rawtime);
    
    strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", timeinfo);
    return buffer;
}

int send_sensor_data(const char* sensor_id, float distance, 
                     const char* server_ip, int port) {
    int sock = 0;
    struct sockaddr_in serv_addr;
    char buffer[BUFFER_SIZE] = {0};
    
    // Create JSON data
    json_t *root = json_object();
    json_object_set_new(root, "sensor_id", json_string(sensor_id));
    json_object_set_new(root, "distance", json_real(distance));
    json_object_set_new(root, "timestamp", json_string(get_timestamp()));
    
    char *json_str = json_dumps(root, 0);
    json_decref(root);
    
    // Create socket
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        printf("Socket creation error\n");
        free(json_str);
        return -1;
    }
    
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(port);
    
    // Convert IPv4 address from text to binary
    if (inet_pton(AF_INET, server_ip, &serv_addr.sin_addr) <= 0) {
        printf("Invalid address/Address not supported\n");
        free(json_str);
        close(sock);
        return -1;
    }
    
    // Connect to server
    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        printf("Connection failed\n");
        free(json_str);
        close(sock);
        return -1;
    }
    
    // Send data
    send(sock, json_str, strlen(json_str), 0);
    
    // Wait for acknowledgment
    int valread = read(sock, buffer, BUFFER_SIZE);
    if (valread > 0 && strncmp(buffer, "ACK", 3) == 0) {
        printf("[%s] Data sent: %.2f cm\n", sensor_id, distance);
    } else {
        printf("[%s] Failed to send data\n", sensor_id);
    }
    
    free(json_str);
    close(sock);
    return 0;
}

void* sensor_thread(void* arg) {
    SensorConfig* config = (SensorConfig*)arg;
    
    printf("Sensor %s started (interval: %d seconds)\n", 
           config->sensor_id, config->interval);
    
    srand(time(NULL) + config->sensor_id[0]);  // Seed for random
    
    while (config->running) {
        float distance = read_sensor_distance();
        
        // Send to server
        if (send_sensor_data(config->sensor_id, distance, 
                            config->server_ip, config->port) < 0) {
            printf("[%s] Connection error, retrying in 5 seconds\n", config->sensor_id);
            sleep(5);
            continue;
        }
        
        sleep(config->interval);
    }
    
    printf("Sensor %s stopped\n", config->sensor_id);
    return NULL;
}

int main(int argc, char const *argv[]) {
    SensorConfig sensors[MAX_SENSORS];
    pthread_t threads[MAX_SENSORS];
    int sensor_count = 3;  // Default 3 sensors
    
    // Configure sensors
    for (int i = 0; i < sensor_count; i++) {
        snprintf(sensors[i].sensor_id, sizeof(sensors[i].sensor_id), 
                "sensor_%02d", i + 1);
        strcpy(sensors[i].server_ip, "127.0.0.1");
        sensors[i].port = PORT;
        sensors[i].interval = 2;  // 2 seconds interval
        sensors[i].running = 1;
    }
    
    // Start sensor threads
    for (int i = 0; i < sensor_count; i++) {
        if (pthread_create(&threads[i], NULL, sensor_thread, &sensors[i]) != 0) {
            perror("Failed to create thread");
            return 1;
        }
        usleep(500000);  // Stagger start times
    }
    
    printf("Press Enter to stop all sensors...\n");
    getchar();
    
    // Stop all sensors
    for (int i = 0; i < sensor_count; i++) {
        sensors[i].running = 0;
    }
    
    // Wait for threads to finish
    for (int i = 0; i < sensor_count; i++) {
        pthread_join(threads[i], NULL);
    }
    
    printf("All sensors stopped\n");
    return 0;
}
