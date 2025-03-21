import os
import sys
import cv2
import numpy as np
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
import webbrowser
from urllib.parse import parse_qs, urlparse

# Add the parent directory to sys.path to import eyeGestures
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import eye tracking modules
try:
    from eyeGestures.utils import VideoCapture
    from eyeGestures import EyeGestures_v3
except ImportError as e:
    print(f"Error importing eye tracking library: {e}")
    print("Please make sure the eyeGestures package is installed correctly.")
    sys.exit(1)

# Global variables
tracker = None
tracking_active = False
calibration_active = False
gaze_point = (0, 0)
current_color = "None"

# Web directory path
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")

# Screen dimensions
screen_width = 1920  # Default, will be updated
screen_height = 1080  # Default, will be updated

def get_screen_dimensions():
    """Get the screen dimensions using screeninfo."""
    global screen_width, screen_height
    try:
        from screeninfo import get_monitors
        monitor = get_monitors()[0]
        screen_width, screen_height = monitor.width, monitor.height
        print(f"Screen dimensions: {screen_width}x{screen_height}")
    except Exception as e:
        print(f"Error getting screen dimensions: {e}")
        print("Using default dimensions: 1920x1080")

def initialize_eye_tracker():
    """Initialize the eye tracking system."""
    global tracker
    try:
        # Initialize eye tracker
        tracker = EyeGestures_v3()
        
        # Create calibration grid (same as in main.py)
        x = np.arange(0, 1.1, 0.2)
        y = np.arange(0, 1.1, 0.2)
        xx, yy = np.meshgrid(x, y)
        calibration_points = np.column_stack([xx.ravel(), yy.ravel()])
        np.random.shuffle(calibration_points)
        n_points = min(len(calibration_points), 25)
        calibration_points = calibration_points[:n_points]
        
        # Upload calibration map
        tracker.uploadCalibrationMap(calibration_points, context="web_ui")
        
        # Set fixation threshold
        tracker.setFixation(1.0)
        
        print("Eye tracker initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing eye tracker: {e}")
        return False

def start_tracking():
    """Start the eye tracking process."""
    global tracking_active, gaze_point, current_color, tracker
    
    # If tracking is already active, don't start again
    if tracking_active:
        print("Tracking is already active")
        return
    
    # Open camera
    cap = None
    try:
        cap = VideoCapture(1)  # Hardcoded to camera index 1
        ret, test_frame = cap.read()
        if ret:
            print("Successfully opened camera 1")
        else:
            print("Could not get frame from camera 1")
            if cap is not None:
                cap.release()
                cap = None
    except Exception as e:
        print(f"Failed to open camera 1: {e}")
        if cap is not None:
            cap.release()
            cap = None
    
    if cap is None:
        print("Could not open camera. Exiting.")
        return
    
    # Set tracking flag and print debug info
    tracking_active = True
    print("Eye tracking started")
    print(f"Screen dimensions: {screen_width}x{screen_height}")
    
    # Initialize average gaze point for smoother tracking
    avg_gaze = None
    alpha = 0.7  # Smoothing factor (higher means more weight on new values)
    
    # Start tracking loop
    try:
        while tracking_active:
            # Get frame from camera
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame")
                time.sleep(0.1)
                continue
            
            # Process frame for eye tracking
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.flip(frame, axis=1)  # Mirror
            
            # Process frame through eye tracking system
            eye_event, _ = tracker.step(
                frame, False, screen_width, screen_height, context="web_ui"
            )
            
            # Process gaze point
            if eye_event is not None:
                # Get raw gaze point
                raw_gaze = (eye_event.point[0], eye_event.point[1])
                
                # Apply smoothing
                if avg_gaze is None:
                    avg_gaze = raw_gaze
                else:
                    avg_gaze = (
                        alpha * raw_gaze[0] + (1 - alpha) * avg_gaze[0],
                        alpha * raw_gaze[1] + (1 - alpha) * avg_gaze[1]
                    )
                
                # Update gaze point
                old_gaze = gaze_point
                gaze_point = (int(avg_gaze[0]), int(avg_gaze[1]))
                
                # Only print when gaze changes significantly to avoid log spam
                if abs(old_gaze[0] - gaze_point[0]) > 10 or abs(old_gaze[1] - gaze_point[1]) > 10:
                    print(f"Gaze point detected: {gaze_point}")
                
                # Check which block is being looked at
                detect_color_block(gaze_point)
            
            time.sleep(0.01)  # Small delay to prevent high CPU usage
    
    except Exception as e:
        print(f"Error during tracking: {e}")
    finally:
        if cap is not None:
            cap.release()
        tracking_active = False
        print("Tracking stopped")

def perform_calibration():
    """Perform eye tracking calibration using the web interface."""
    global calibration_active, tracking_active, tracker
    
    # Temporarily stop tracking if active
    was_tracking = tracking_active
    tracking_active = False
    time.sleep(0.5)  # Wait for tracking to stop
    
    # Open camera
    cap = None
    try:
        cap = VideoCapture(1)  # Hardcoded to camera index 1
        ret, test_frame = cap.read()
        if ret:
            print("Successfully opened camera 1")
        else:
            print("Could not get frame from camera 1")
            if cap is not None:
                cap.release()
                cap = None
    except Exception as e:
        print(f"Failed to open camera 1: {e}")
        if cap is not None:
            cap.release()
            cap = None
    
    if cap is None:
        print("Could not open camera. Exiting calibration.")
        calibration_active = False  # Ensure flag is properly reset
        return
    
    # Set calibration flag
    calibration_active = True
    print("Calibration started")
    
    # Use a smaller number of calibration points for better UX
    calibration_points = [
        (0.1, 0.1),  # Top left
        (0.5, 0.1),  # Top center
        (0.9, 0.1),  # Top right
        (0.1, 0.5),  # Middle left
        (0.5, 0.5),  # Center
        (0.9, 0.5),  # Middle right
        (0.1, 0.9),  # Bottom left
        (0.5, 0.9),  # Bottom center
        (0.9, 0.9),  # Bottom right
    ]
    n_points = len(calibration_points)
    
    # Start calibration loop
    try:
        # Process each calibration point in order
        for i, (norm_x, norm_y) in enumerate(calibration_points):
            if not calibration_active:
                print("Calibration was cancelled")
                break
                
            # Calculate screen coordinates
            point_x = int(norm_x * screen_width)
            point_y = int(norm_y * screen_height)
            
            print(f"Calibration point {i+1}/{n_points} at ({point_x}, {point_y})")
            
            # Allow 1.8 seconds for each point (matching the frontend timing)
            start_time = time.time()
            while time.time() - start_time < 1.8 and calibration_active:
                # Get frame from camera
                ret, frame = cap.read()
                if not ret:
                    print("Failed to capture frame")
                    time.sleep(0.1)
                    continue
                
                # Process frame for eye tracking
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.flip(frame, axis=1)  # Mirror
                
                # Process frame through eye tracking system with calibration
                tracker.step(
                    frame, True, screen_width, screen_height, 
                    fixation_point=(point_x, point_y), context="web_ui"
                )
                
                # Small delay to prevent high CPU usage
                time.sleep(0.01)
    
    except Exception as e:
        print(f"Error during calibration: {e}")
    finally:
        if cap is not None:
            cap.release()
        
        # Ensure we always reset the calibration flag
        calibration_active = False
        print("Calibration completed")
        
        # Resume tracking if it was active before
        if was_tracking:
            threading.Thread(target=start_tracking, daemon=True).start()

def detect_color_block(point):
    """Detect which colored block contains the gaze point."""
    global current_color
    
    # Skip invalid points
    if point[0] == 0 and point[1] == 0:
        return
    
    # These values need to be adjusted based on the actual browser window size
    # For now, we'll assume the browser takes up 90% of the screen width and 85% of the height
    browser_width = screen_width * 0.9
    browser_height = screen_height * 0.85
    
    # Estimate the position of the browser window (centered on screen)
    browser_left = (screen_width - browser_width) / 2
    browser_top = (screen_height - browser_height) * 0.2  # Assume browser starts at 20% of the available space from top
    
    # Calculate where the main content area starts (excluding header)
    content_top = browser_top + 120  # Estimate header height ~120px
    content_height = browser_height * 0.7  # content area is about 70% of browser height
    content_width = browser_width * 0.9  # content width is about 90% of browser width
    content_left = browser_left + (browser_width - content_width) / 2
    
    # Debug info on layout
    # print(f"Browser window: Left={browser_left}, Top={browser_top}, Width={browser_width}, Height={browser_height}")
    # print(f"Content area: Left={content_left}, Top={content_top}, Width={content_width}, Height={content_height}")
    
    # Check if the gaze point is within the browser window
    if (browser_left <= point[0] <= browser_left + browser_width and
        browser_top <= point[1] <= browser_top + browser_height):
        
        # Calculate relative position within content area
        rel_x = (point[0] - content_left) / content_width
        rel_y = (point[1] - content_top) / content_height
        
        # Only process when coordinates are in a reasonable range
        if 0 <= rel_x <= 1 and 0 <= rel_y <= 1:
            # Less frequent logging to reduce spam
            # print(f"Gaze in content area: ({rel_x:.2f}, {rel_y:.2f})")
            
            # Store previous color for change detection
            old_color = current_color
            
            # Determine which block is being looked at based on 2x2 grid
            if 0 <= rel_x < 0.5 and 0 <= rel_y < 0.5:
                current_color = "Red"
            elif 0.5 <= rel_x <= 1.0 and 0 <= rel_y < 0.5:
                current_color = "Blue"
            elif 0 <= rel_x < 0.5 and 0.5 <= rel_y <= 1.0:
                current_color = "Green"
            elif 0.5 <= rel_x <= 1.0 and 0.5 <= rel_y <= 1.0:
                current_color = "Yellow"
            else:
                current_color = "None"
                
            # Print when the looked at color changes
            if old_color != current_color:
                print(f"Looking at: {current_color} (at relative position {rel_x:.2f}, {rel_y:.2f})")
        else:
            # Point is outside the main content area
            if current_color != "None":
                current_color = "None"
                print("Gaze outside content area")
    else:
        # Point is outside the browser window
        if current_color != "None":
            current_color = "None"
            print("Gaze outside browser window")

# HTTP Server to serve the web files and handle API requests
class EyeTrackerHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type="text/html"):
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
    
    def _serve_file(self, path, content_type):
        try:
            with open(path, 'rb') as file:
                self.send_response(200)
                self.send_header("Content-type", content_type)
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"File not found")
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/" or path == "/index.html":
            self._serve_file(os.path.join(WEB_DIR, "index.html"), "text/html")
        elif path.endswith(".css"):
            self._serve_file(os.path.join(WEB_DIR, path[1:]), "text/css")
        elif path.endswith(".js"):
            self._serve_file(os.path.join(WEB_DIR, path[1:]), "application/javascript")
        elif path == "/api/status":
            self._set_headers("application/json")
            status = {
                "tracking": tracking_active,
                "calibration": calibration_active,
                "gaze": {"x": gaze_point[0], "y": gaze_point[1]},
                "color": current_color
            }
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        global tracking_active, calibration_active
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        parsed_data = parse_qs(post_data)
        
        if self.path == "/api/start":
            print("Received start tracking request")
            if not tracking_active:
                print("Starting tracking thread")
                threading.Thread(target=start_tracking, daemon=True).start()
                self._set_headers("application/json")
                self.wfile.write(json.dumps({"status": "started"}).encode())
            else:
                print("Tracking already active")
                self._set_headers("application/json")
                self.wfile.write(json.dumps({"status": "already_running"}).encode())
        
        elif self.path == "/api/stop":
            print("Received stop tracking request")
            tracking_active = False
            self._set_headers("application/json")
            self.wfile.write(json.dumps({"status": "stopped"}).encode())
        
        elif self.path == "/api/calibrate":
            print("Received calibration request")
            if not calibration_active:
                threading.Thread(target=perform_calibration, daemon=True).start()
                self._set_headers("application/json")
                self.wfile.write(json.dumps({"status": "calibration_started"}).encode())
            else:
                print("Calibration already in progress")
                self._set_headers("application/json")
                self.wfile.write(json.dumps({"status": "already_calibrating"}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()

def start_server(port=8000):
    """Start the HTTP server."""
    max_attempts = 5
    attempt = 0
    
    while attempt < max_attempts:
        try:
            server_address = ('', port)
            
            # Use ThreadingHTTPServer to handle multiple requests
            class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
                pass
            
            httpd = ThreadingHTTPServer(server_address, EyeTrackerHandler)
            print(f"Starting server on port {port}...")
            
            # Open the web page in a browser
            webbrowser.open(f"http://localhost:{port}")
            
            # Run the server
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                httpd.server_close()
                print("Server stopped")
            
            # If we get here, the server ran and stopped normally
            break
            
        except OSError as e:
            if e.errno == 48:  # Address already in use
                attempt += 1
                port += 1
                print(f"Port {port-1} is in use, trying port {port}...")
            else:
                print(f"Error starting server: {e}")
                break

if __name__ == "__main__":
    # Get screen dimensions
    get_screen_dimensions()
    
    # Initialize eye tracker
    if initialize_eye_tracker():
        # Start server
        start_server()
    else:
        print("Failed to initialize eye tracker. Exiting.")