# dashboard.py
import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import queue
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import websocket
import csv
import pandas as pd
from collections import deque

class ProximityDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Proximity Sensor Dashboard")
        self.root.geometry("1400x900")
        
        # WebSocket connection
        self.ws_url = "ws://localhost:8080/sensors"
        self.ws = None
        self.ws_connected = False
        
        # Data storage
        self.sensor_data = {}
        self.history_length = 50
        self.sensor_history = {}
        
        # Colors for status
        self.status_colors = {
            "SAFE": "#4CAF50",
            "CAUTION": "#FF9800",
            "WARNING": "#f44336",
            "CRITICAL": "#9C27B0"
        }
        
        # Initialize UI
        self.setup_ui()
        
        # Start WebSocket in separate thread
        self.start_websocket()
        
        # Start update loop
        self.update_dashboard()
        
        # Load historical data
        self.load_historical_data()
    
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        ttk.Label(
            header_frame, 
            text="Proximity Sensor Monitoring System",
            font=("Arial", 24, "bold")
        ).pack()
        
        # Status indicator
        self.status_label = ttk.Label(
            header_frame,
            text="Connecting...",
            font=("Arial", 12)
        )
        self.status_label.pack()
        
        # Sensor grid frame
        self.sensor_frame = ttk.Frame(main_frame)
        self.sensor_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Charts frame
        chart_frame = ttk.LabelFrame(main_frame, text="Distance History", padding="10")
        chart_frame.grid(row=2, column=0, pady=20, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Initialize matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(12, 4))
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Distance (cm)')
        self.ax.set_title('Sensor Distance Over Time')
        self.ax.grid(True, alpha=0.3)
        
        # Embed matplotlib in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=3, column=0, pady=10)
        
        ttk.Button(
            controls_frame,
            text="Refresh Connection",
            command=self.reconnect_websocket
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            controls_frame,
            text="Export Data",
            command=self.export_data
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            controls_frame,
            text="Settings",
            command=self.show_settings
        ).pack(side=tk.LEFT, padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Event Log", padding="10")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Log text widget with scrollbar
        self.log_text = tk.Text(log_frame, height=8, width=100)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Initialize sensor widgets dictionary
        self.sensor_widgets = {}
    
    def create_sensor_widget(self, sensor_id):
        """Create a widget for a sensor"""
        frame = ttk.LabelFrame(
            self.sensor_frame, 
            text=f"Sensor: {sensor_id}",
            padding="10"
        )
        
        # Status indicator
        status_frame = ttk.Frame(frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        status_label = ttk.Label(status_frame, text="Status:", font=("Arial", 10))
        status_label.pack(side=tk.LEFT)
        
        status_value = ttk.Label(
            status_frame, 
            text="UNKNOWN", 
            font=("Arial", 10, "bold")
        )
        status_value.pack(side=tk.LEFT, padx=5)
        
        # Distance display
        distance_frame = ttk.Frame(frame)
        distance_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(distance_frame, text="Distance:", font=("Arial", 10)).pack(side=tk.LEFT)
        
        distance_value = ttk.Label(
            distance_frame, 
            text="0.00", 
            font=("Arial", 20, "bold")
        )
        distance_value.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(distance_frame, text="cm", font=("Arial", 10)).pack(side=tk.LEFT)
        
        # Progress bar
        progress = ttk.Progressbar(
            frame, 
            length=200, 
            mode='determinate',
            maximum=100
        )
        progress.pack(fill=tk.X, pady=(0, 10))
        
        # Timestamp
        timestamp_label = ttk.Label(
            frame, 
            text="Last update: Never",
            font=("Arial", 8)
        )
        timestamp_label.pack()
        
        # Store widgets
        self.sensor_widgets[sensor_id] = {
            'frame': frame,
            'status': status_value,
            'distance': distance_value,
            'progress': progress,
            'timestamp': timestamp_label
        }
        
        return frame
    
    def start_websocket(self):
        """Start WebSocket connection in separate thread"""
        def ws_thread():
            while True:
                try:
                    self.log_message("Connecting to WebSocket server...")
                    self.ws = websocket.WebSocketApp(
                        self.ws_url,
                        on_message=self.on_ws_message,
                        on_error=self.on_ws_error,
                        on_close=self.on_ws_close,
                        on_open=self.on_ws_open
                    )
                    self.ws.run_forever()
                except Exception as e:
                    self.log_message(f"WebSocket error: {e}")
                    time.sleep(5)  # Wait before reconnecting
        
        thread = threading.Thread(target=ws_thread, daemon=True)
        thread.start()
    
    def on_ws_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            self.sensor_data = data
            
            # Update history
            for sensor_id, sensor_info in data.items():
                if sensor_id not in self.sensor_history:
                    self.sensor_history[sensor_id] = deque(maxlen=self.history_length)
                
                self.sensor_history[sensor_id].append({
                    'timestamp': datetime.now(),
                    'distance': sensor_info.get('distance', 0),
                    'status': sensor_info.get('status', 'UNKNOWN')
                })
            
        except json.JSONDecodeError as e:
            self.log_message(f"JSON decode error: {e}")
    
    def on_ws_error(self, ws, error):
        """Handle WebSocket errors"""
        self.ws_connected = False
        self.status_label.config(text="Disconnected", foreground="red")
        self.log_message(f"WebSocket error: {error}")
    
    def on_ws_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket closure"""
        self.ws_connected = False
        self.status_label.config(text="Disconnected", foreground="red")
        self.log_message("WebSocket connection closed")
    
    def on_ws_open(self, ws):
        """Handle WebSocket opening"""
        self.ws_connected = True
        self.status_label.config(text="Connected", foreground="green")
        self.log_message("WebSocket connection established")
    
    def update_dashboard(self):
        """Update the dashboard with latest data"""
        # Clear current sensor widgets
        for widget in self.sensor_frame.winfo_children():
            widget.destroy()
        
        # Create or update sensor widgets
        row, col = 0, 0
        max_cols = 3
        
        for sensor_id, sensor_info in self.sensor_data.items():
            if sensor_id not in self.sensor_widgets:
                self.create_sensor_widget(sensor_id)
            
            widgets = self.sensor_widgets[sensor_id]
            
            # Update widget values
            distance = sensor_info.get('distance', 0)
            status = sensor_info.get('status', 'UNKNOWN')
            timestamp = sensor_info.get('timestamp', 'Unknown')
            
            # Update status
            widgets['status'].config(
                text=status,
                foreground=self.status_colors.get(status, 'black')
            )
            
            # Update distance
            widgets['distance'].config(text=f"{distance:.2f}")
            
            # Update progress bar
            widgets['progress']['value'] = min(distance, 100)
            widgets['progress']['style'] = f"{status.lower()}.Horizontal"
            
            # Update timestamp
            widgets['timestamp'].config(text=f"Last update: {timestamp}")
            
            # Place widget in grid
            widgets['frame'].grid(
                row=row, 
                column=col, 
                padx=10, 
                pady=10, 
                sticky=(tk.W, tk.E, tk.N, tk.S)
            )
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Update chart
        self.update_chart()
        
        # Schedule next update
        self.root.after(1000, self.update_dashboard)
    
    def update_chart(self):
        """Update the distance history chart"""
        self.ax.clear()
        
        colors = plt.cm.Set3(range(len(self.sensor_history)))
        
        for idx, (sensor_id, history) in enumerate(self.sensor_history.items()):
            if history:
                timestamps = [entry['timestamp'] for entry in history]
                distances = [entry['distance'] for entry in history]
                
                self.ax.plot(
                    timestamps, 
                    distances, 
                    label=sensor_id,
                    color=colors[idx],
                    linewidth=2,
                    marker='o',
                    markersize=4
                )
        
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Distance (cm)')
        self.ax.set_title('Sensor Distance Over Time')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper right')
        
        # Rotate x-axis labels for better readability
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)
        
        self.canvas.draw()
    
    def load_historical_data(self):
        """Load historical data from CSV file"""
        try:
            df = pd.read_csv('sensor_data.csv')
            for _, row in df.iterrows():
                sensor_id = row['sensor_id']
                if sensor_id not in self.sensor_history:
                    self.sensor_history[sensor_id] = deque(maxlen=self.history_length)
                
                self.sensor_history[sensor_id].append({
                    'timestamp': pd.to_datetime(row['timestamp']),
                    'distance': float(row['distance']),
                    'status': row['status']
                })
            
            self.log_message("Historical data loaded successfully")
        except FileNotFoundError:
            self.log_message("No historical data found")
        except Exception as e:
            self.log_message(f"Error loading historical data: {e}")
    
    def export_data(self):
        """Export current data to CSV"""
        try:
            filename = f"sensor_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Sensor ID', 'Distance', 'Status', 'Timestamp'])
                
                for sensor_id, sensor_info in self.sensor_data.items():
                    writer.writerow([
                        sensor_id,
                        sensor_info.get('distance', 0),
                        sensor_info.get('status', 'UNKNOWN'),
                        sensor_info.get('timestamp', '')
                    ])
            
            self.log_message(f"Data exported to {filename}")
            messagebox.showinfo("Export Successful", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {e}")
    
    def reconnect_websocket(self):
        """Reconnect to WebSocket server"""
        if self.ws:
            self.ws.close()
        self.start_websocket()
        self.log_message("Attempting to reconnect...")
    
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        
        ttk.Label(settings_window, text="WebSocket URL:").pack(pady=10)
        url_var = tk.StringVar(value=self.ws_url)
        url_entry = ttk.Entry(settings_window, textvariable=url_var, width=40)
        url_entry.pack()
        
        ttk.Label(settings_window, text="History Length:").pack(pady=10)
        history_var = tk.IntVar(value=self.history_length)
        history_spinbox = ttk.Spinbox(
            settings_window, 
            from_=10, 
            to=1000, 
            textvariable=history_var,
            width=10
        )
        history_spinbox.pack()
        
        def save_settings():
            self.ws_url = url_var.get()
            self.history_length = history_var.get()
            
            # Update all history deques
            for sensor_id in self.sensor_history:
                old_deque = self.sensor_history[sensor_id]
                new_deque = deque(maxlen=self.history_length)
                new_deque.extend(old_deque)
                self.sensor_history[sensor_id] = new_deque
            
            settings_window.destroy()
            self.log_message("Settings saved")
            self.reconnect_websocket()
        
        ttk.Button(settings_window, text="Save", command=save_settings).pack(pady=20)
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)  # Auto-scroll to bottom
        self.log_text.update()
    
    def on_closing(self):
        """Handle application closing"""
        if self.ws:
            self.ws.close()
        self.root.destroy()

def main():
    root = tk.Tk()
    
    # Create custom styles for progress bars
    style = ttk.Style()
    style.theme_use('clam')
    
    # Define progress bar colors for different statuses
    style.configure("safe.Horizontal.TProgressbar", background='#4CAF50')
    style.configure("caution.Horizontal.TProgressbar", background='#FF9800')
    style.configure("warning.Horizontal.TProgressbar", background='#f44336')
    style.configure("critical.Horizontal.TProgressbar", background='#9C27B0')
    
    app = ProximityDashboard(root)
    
    # Set closing protocol
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.mainloop()

if __name__ == "__main__":
    main()
