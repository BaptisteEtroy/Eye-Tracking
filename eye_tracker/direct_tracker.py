import os
import sys
import importlib.util
import threading
import time
import webbrowser
import cv2
import numpy as np
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
import json
from urllib.parse import parse_qs, urlparse

# Add the parent directory to sys.path to import main.py components
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Global variables for API
tracking_active = False
calibration_active = False
current_color = "None"
gaze_point = (0, 0)

# Web directory path
WEB_DIR = os.path.join(parent_dir, "web")

# Import eyeGestures components directly (like main.py does)
try:
    from eyeGestures.utils import VideoCapture
    from eyeGestures import EyeGestures_v3
    
    # Initialize the eye tracking system like in main.py
    gestures = EyeGestures_v3()
    
    # Get display dimensions - use same approach as main.py
    try:
        from screeninfo import get_monitors
        monitor = get_monitors()[0]
        display_width, display_height = monitor.width, monitor.height
        print(f"Using screen resolution: {display_width}x{display_height}")
    except:
        # Fallback to standard resolution
        display_width = 1920
        display_height = 1080
        print(f"Using default resolution: {display_width}x{display_height}")
    
    # Create and set up calibration points exactly like main.py
    # Create calibration grid (6x6 points evenly distributed)
    x = np.linspace(0.1, 0.9, 6)  # Avoid extreme edges
    y = np.linspace(0.1, 0.9, 6)  # Avoid extreme edges
    xx, yy = np.meshgrid(x, y)
    calibration_points = np.column_stack([xx.ravel(), yy.ravel()])

    # Shuffle points to avoid predictable patterns
    np.random.shuffle(calibration_points)

    # Set maximum number of calibration points to use
    max_calibration_points = 25
    n_points = min(len(calibration_points), max_calibration_points)
    calibration_points = calibration_points[:n_points]
    
    # Upload calibration map to the eye tracking system
    gestures.uploadCalibrationMap(calibration_points, context="calibration")
    
    # Set fixation threshold (higher = more stable but less reactive)
    gestures.setFixation(1.0)
    
    print("Eye tracking initialized successfully")
    
except ImportError as e:
    print(f"Error importing eye tracking library: {e}")
    print("Please make sure the eyeGestures package is installed correctly.")
    sys.exit(1)
except Exception as e:
    print(f"Error initializing eye tracking: {e}")
    print("Please check your camera and eye tracking setup.")
    sys.exit(1)

# Function to detect which color block is being looked at
def detect_color_block(point):
    """Detect which colored block contains the gaze point."""
    global current_color
    
    # Simple quadrant detection - exactly like the approach used in main.py
    center_x = display_width / 2
    center_y = display_height / 2
    
    if point[0] < center_x and point[1] < center_y:
        new_color = "Red"
    elif point[0] >= center_x and point[1] < center_y:
        new_color = "Blue"
    elif point[0] < center_x and point[1] >= center_y:
        new_color = "Green"
    elif point[0] >= center_x and point[1] >= center_y:
        new_color = "Yellow"
    else:
        new_color = "None"
    
    # Only update if color changed
    if new_color != current_color:
        current_color = new_color
        print(f"Looking at: {current_color}")

# Function to start tracking
def start_tracking():
    """Start the eye tracking process."""
    global tracking_active, gaze_point, current_color
    
    # Open camera - exactly like main.py
    try:
        cap = VideoCapture(1)  # using camera 1
        ret, test_frame = cap.read()
        if not ret:
            print("Failed to open camera 1")
            return
    except Exception as e:
        print(f"Error opening camera 1: {e}")
        return
    
    tracking_active = True
    
    # Start tracking loop - optimized for speed
    try:
        while tracking_active:
            # Get frame from camera
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame")
                continue
            
            # Process frame exactly like main.py
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.flip(frame, axis=1)  # Mirror
            
            # Process frame - no calibration needed during tracking
            eye_event, _ = gestures.step(
                frame, False, display_width, display_height, context="calibration"
            )
            
            # Process gaze point immediately
            if eye_event is not None and eye_event.point is not None:
                # Get gaze point just like main.py
                gaze_point = (int(eye_event.point[0]), int(eye_event.point[1]))
                
                # Detect which color block is being looked at
                detect_color_block(gaze_point)
                print(f"Gaze point: {gaze_point}, Looking at: {current_color}, Fixation: {eye_event.fixation:.2f}")
    
    except Exception as e:
        print(f"Error during tracking: {e}")
    finally:
        tracking_active = False
        print("Tracking stopped")

# Function to run calibration with the exact UI from main.py
def run_calibration():
    """Run the calibration with the same UI as main.py."""
    global tracking_active, calibration_active
    
    # Stop tracking if it's active
    was_tracking = tracking_active
    if tracking_active:
        tracking_active = False
        time.sleep(0.5)  # Wait for tracking to stop
    
    calibration_active = True
    try:
        # Open camera
        cap = VideoCapture(1)  # using camera 1
        ret, test_frame = cap.read()
        if not ret:
            print("Failed to open camera 1")
            calibration_active = False
            return
        
        try:
            # Create named window and set to fullscreen - exactly like main.py
            cv2.namedWindow("Eye Tracking Calibration", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("Eye Tracking Calibration", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        except Exception as window_error:
            print(f"Error creating OpenCV window: {window_error}")
            print("Continuing with calibration without fullscreen window")
        
        # Initialize variables for tracking calibration progress
        iterator = 0
        prev_x, prev_y = 0, 0
        calibration_complete = False
        
        # Helper function to draw text on image (from main.py)
        def draw_text(img, text, position, color=(255, 255, 255), scale=1.0, thickness=2):
            cv2.putText(img, text, position, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)
        
        # Helper function to ensure point format (from main.py)
        def ensure_point_format(point):
            if point is None:
                return (0, 0)
            
            try:
                # Handle different types of input
                if isinstance(point, tuple) and len(point) == 2:
                    return (int(point[0]), int(point[1]))
                elif isinstance(point, list) and len(point) == 2:
                    return (int(point[0]), int(point[1]))
                elif hasattr(point, '__getitem__') and len(point) >= 2:
                    return (int(point[0]), int(point[1]))
                elif hasattr(point, 'x') and hasattr(point, 'y'):
                    return (int(point.x), int(point.y))
                else:
                    print(f"Unknown point format: {type(point)} - {point}")
                    return (0, 0)
            except Exception as e:
                print(f"Error converting point: {e} - {type(point)} - {point}")
                return (0, 0)
        
        print("Beginning calibration sequence")
        start_time = time.time()
        
        # Main calibration loop - directly from main.py
        while calibration_active and not calibration_complete and (time.time() - start_time) < 60:
            # Get frame from camera
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame")
                time.sleep(0.1)
                continue
            
            # Create display frame - black background
            display = np.zeros((display_height, display_width, 3), dtype=np.uint8)
            
            try:
                # Process frame for eye tracking
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.flip(frame, axis=1)  # Mirror
                
                # Determine if we're in calibration mode
                calibrate = not calibration_complete and (iterator < n_points)
                
                # Process frame through eye tracking system
                eye_event, calibration_event = gestures.step(
                    frame, calibrate, display_width, display_height, context="calibration"
                )
                
                # If eye tracking is working
                if eye_event is not None:
                    # Handle calibration
                    if calibrate and calibration_event is not None:
                        # Get center point in proper format for circle drawing
                        center_point = ensure_point_format(calibration_event.point)
                        radius = int(getattr(calibration_event, 'acceptance_radius', 20))
                        
                        # Draw the current calibration target - exactly like main.py
                        cv2.circle(display, center_point, radius, (255, 0, 0), 2)  # Blue circle
                        cv2.circle(display, center_point, 5, (0, 0, 255), -1)      # Red center
                        
                        # Show progress
                        progress_text = f"Calibration: {iterator+1}/{n_points}"
                        draw_text(display, progress_text, (display_width//2 - 100, 40), scale=1.5, thickness=2)
                        
                        # Update calibration progress
                        if calibration_event.point is not None:
                            new_x, new_y = center_point
                            if (new_x != prev_x or new_y != prev_y) and new_x > 0 and new_y > 0:
                                iterator += 1
                                prev_x, prev_y = new_x, new_y
                                print(f"Calibration point {iterator}/{n_points} at {center_point}")
                                
                                # Check if calibration is complete
                                if iterator >= n_points:
                                    calibration_complete = True
                                    print("Calibration complete!")
                
                # Display instructions
                instructions = [
                    "Look at the blue circles during calibration",
                    "Press ESC to exit"
                ]
                
                for i, instruction in enumerate(instructions):
                    draw_text(display, instruction, (20, display_height - 100 + (i * 30)))
                
                # Show the display
                try:
                    cv2.imshow("Eye Tracking Calibration", display)
                    
                    # Handle keyboard input - check for ESC to exit
                    key = cv2.waitKey(1) & 0xFF
                    if key == 27:  # ESC
                        break
                except Exception as cv_error:
                    print(f"Error displaying calibration: {cv_error}")
                    break
                    
            except Exception as frame_error:
                print(f"Error processing frame: {frame_error}")
                time.sleep(0.1)
        
    except Exception as e:
        print(f"Error during calibration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            cv2.destroyAllWindows()
        except:
            pass
        
        calibration_active = False
        print("Calibration ended")
        
        # Restart tracking if it was active before
        if was_tracking:
            threading.Thread(target=start_tracking, daemon=True).start()

# Add this simpler calibration function
def run_simple_calibration():
    """Run a simplified calibration without requiring OpenCV windows."""
    global tracking_active, calibration_active
    
    # Stop tracking if it's active
    was_tracking = tracking_active
    if tracking_active:
        tracking_active = False
        time.sleep(0.5)  # Wait for tracking to stop
    
    calibration_active = True
    print("Starting simplified calibration process...")
    
    try:
        # Open camera
        cap = VideoCapture(1)  # using camera 1
        ret, test_frame = cap.read()
        if not ret:
            print("Failed to open camera 1")
            calibration_active = False
            return
        
        # Initialize calibration variables
        iterator = 0
        start_time = time.time()
        
        # Use webbrowser to open a calibration page that will show the dots
        webbrowser.open(f"http://localhost:8000/calibration.html")
        
        # Give the browser a moment to open
        time.sleep(1)
        
        # Process frames for calibration
        while calibration_active and iterator < n_points and (time.time() - start_time) < 60:
            # Get frame from camera
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame")
                time.sleep(0.1)
                continue
            
            # Process frame for eye tracking
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.flip(frame, axis=1)  # Mirror
            
            # Run calibration step
            eye_event, calibration_event = gestures.step(
                frame, True, display_width, display_height, context="calibration"
            )
            
            # Track progress
            if calibration_event is not None and calibration_event.point is not None:
                # Get the current calibration point
                point_x = int(calibration_event.point[0])
                point_y = int(calibration_event.point[1])
                
                # Only increment if we have a new point
                if point_x > 0 and point_y > 0:
                    iterator += 1
                    print(f"Calibration point {iterator}/{n_points} at ({point_x}, {point_y})")
                    
                    # Short delay between points
                    time.sleep(0.05)
            
            # Brief pause to reduce CPU usage
            time.sleep(0.01)
        
        if iterator >= n_points:
            print("Calibration complete!")
        else:
            print(f"Calibration incomplete: {iterator}/{n_points} points processed")
        
    except Exception as e:
        print(f"Error during simplified calibration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        calibration_active = False
        print("Calibration ended")
        
        # Restart tracking if it was active before
        if was_tracking:
            threading.Thread(target=start_tracking, daemon=True).start()
            
    return

# Function to directly run main.py's calibration
def run_main_calibration():
    """Directly execute main.py for calibration"""
    global calibration_active
    
    calibration_active = True
    print("Starting main.py calibration...")
    
    try:
        # Get the path to main.py
        main_py_path = os.path.join(parent_dir, "main.py")
        
        # Run main.py as a subprocess
        import subprocess
        
        # Create the subprocess
        proc = subprocess.Popen([sys.executable, main_py_path])
        
        # Wait for the calibration to complete
        proc.wait()
        
        print("main.py calibration completed")
    except Exception as e:
        print(f"Error running main.py calibration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        calibration_active = False
        print("Calibration process ended")
    
    return

# HTTP Server to serve the web files and handle API requests
class DirectTrackerHandler(BaseHTTPRequestHandler):
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
    
    # Override to silence logging for faster processing
    def log_message(self, format, *args):
        pass
    
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
            
            # Determine the overall status
            if calibration_active:
                status = "calibrating"
            elif tracking_active:
                status = "tracking"
            else:
                status = "ready"
            
            status_data = {
                "status": status,
                "tracking": tracking_active,
                "calibration": calibration_active,
                "color": current_color
            }
            self.wfile.write(json.dumps(status_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        global tracking_active
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        if self.path == "/api/start":
            if not tracking_active:
                threading.Thread(target=start_tracking, daemon=True).start()
                self._set_headers("application/json")
                self.wfile.write(json.dumps({"status": "started"}).encode())
            else:
                self._set_headers("application/json")
                self.wfile.write(json.dumps({"status": "already_running"}).encode())
        
        elif self.path == "/api/stop":
            tracking_active = False
            self._set_headers("application/json")
            self.wfile.write(json.dumps({"status": "stopped"}).encode())
        
        elif self.path == "/api/calibrate":
            # Run main.py directly for calibration
            threading.Thread(target=run_main_calibration, daemon=True).start()
            self._set_headers("application/json")
            self.wfile.write(json.dumps({"status": "calibration_started"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

def start_server(port=8000):
    """Start the HTTP server."""
    server_address = ('', port)
    
    # Use ThreadingHTTPServer to handle multiple requests
    class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
        pass
    
    httpd = ThreadingHTTPServer(server_address, DirectTrackerHandler)
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

if __name__ == "__main__":
    # Start server
    start_server() 