import os
import sys
import cv2
import numpy as np
import traceback

# Import the eye tracking library
try:
    from eyeGestures.utils import VideoCapture
    from eyeGestures import EyeGestures_v3
except ImportError as e:
    print(f"Error importing eye tracking library: {e}")
    print("Please make sure the eyeGestures package is installed correctly.")
    sys.exit(1)

# Initialize eye tracking
try:
    gestures = EyeGestures_v3()
except Exception as e:
    print(f"Error initializing eye tracking: {e}")
    print("Please check your camera and eye tracking setup.")
    sys.exit(1)


cap = VideoCapture(1)  # using camera 1
ret, test_frame = cap.read()

if cap is None:
    print("Could not open any camera. Exiting.")
    sys.exit(1)

# Get display dimensions (use system resolution)
try:
    # Get screen resolution
    from screeninfo import get_monitors
    monitor = get_monitors()[0]
    display_width, display_height = monitor.width, monitor.height
    print(f"Using screen resolution: {display_width}x{display_height}")
except:
    # Fallback to standard resolution
    display_width = 1920
    display_height = 1080
    print(f"Using default resolution: {display_width}x{display_height}")

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
try:
    gestures.uploadCalibrationMap(calibration_points, context="calibration")
except Exception as e:
    print(f"Error uploading calibration map: {e}")
    print("Please check your eye tracking setup.")
    cap.release()
    sys.exit(1)

# Set fixation threshold (higher = more stable but less reactive)
gestures.setFixation(1.0)

# Initialize variables for tracking calibration progress
iterator = 0
prev_x, prev_y = 0, 0
calibration_complete = False
calibration_started = False
error_message = None

def draw_text(img, text, position, color=(255, 255, 255), scale=1.0, thickness=2):
    """Helper function to draw text on image"""
    cv2.putText(img, text, position, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)

def draw_start_screen():
    """Draw the start screen with instructions"""
    # Create a black background
    display = np.zeros((display_height, display_width, 3), dtype=np.uint8)
    
    # Draw title
    title = "Eye Tracking Calibration"
    draw_text(display, title, 
             (display_width//2 - 300, 100), 
             scale=2.0, 
             thickness=3)
    
    # Draw instructions
    instructions = [
        "Press SPACE to start calibration",
        "Press ESC to exit",
        "Make sure your face is clearly visible in the camera",
        "Sit at a comfortable distance from the screen",
        "Your camera feed is processed but not displayed"
    ]
    
    for i, instruction in enumerate(instructions):
        draw_text(display, instruction,
                 (display_width//2 - 300, 200 + (i * 50)),
                 scale=1.0,
                 thickness=2)
    
    return display

def draw_error_message(img, message):
    """Draw error message in the center of the screen"""
    draw_text(img, message,
             (display_width//2 - 300, display_height//2),
             color=(0, 0, 255),
             scale=1.5,
             thickness=3)

def ensure_point_format(point):
    """Convert point to the correct format for cv2.circle (tuple of ints)"""
    if point is None:
        return (0, 0)  # Default fallback
    
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
            return (0, 0)  # Default fallback
    except Exception as e:
        print(f"Error converting point: {e} - {type(point)} - {point}")
        return (0, 0)  # Default fallback

# Create named window and set to a large window
cv2.namedWindow("Eye Tracking Calibration", cv2.WINDOW_NORMAL)
# Set window size to almost match screen resolution with minimal margins
cv2.resizeWindow("Eye Tracking Calibration", display_width - 2, display_height - 2)
# Don't use fullscreen mode as it's causing issues
# cv2.setWindowProperty("Eye Tracking Calibration", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Main loop
running = True
while running:
    try:
        # Get frame from camera
        ret, frame = cap.read()
        if not ret:
            error_message = "Failed to capture frame"
            print(error_message)
            continue
        
        # Create display frame
        display = np.zeros((display_height, display_width, 3), dtype=np.uint8)
        
        if not calibration_started:
            display = draw_start_screen()
        else:
            # Process frame for eye tracking
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.flip(frame, axis=1)  # Mirror the frame to make it more intuitive
            
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
                    radius = int(calibration_event.acceptance_radius)
                    
                    # Draw the current calibration target
                    cv2.circle(display,
                             center_point,
                             radius,
                             (255, 0, 0),  # Blue
                             2)
                    
                    # Draw target center
                    cv2.circle(display,
                             center_point,
                             5,
                             (0, 0, 255),  # Red
                             -1)
                    
                    # Show progress
                    progress_text = f"Calibration: {iterator+1}/{n_points}"
                    draw_text(display, progress_text,
                            (display_width//2 - 100, 40),
                            scale=1.5,
                            thickness=2)
                    
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
                
                # Display gaze pointer when not calibrating
                elif calibration_complete:
                    # Get gaze point in proper format
                    gaze_point = ensure_point_format(eye_event.point)
                    
                    # Draw gaze point as circle
                    cv2.circle(display,
                             gaze_point,
                             20,
                             (0, 0, 255),  # Red
                             -1)
                    
                    # Draw gaze algorithm type
                    algo_text = gestures.whichAlgorithm(context="calibration")
                    draw_text(display, f"Algorithm: {algo_text}",
                            (display_width - 300, 30))
                    
                    # Draw fixation value
                    draw_text(display, f"Fixation: {eye_event.fixation:.2f}",
                            (display_width - 300, 60))
            
            # Display instructions
            instructions = [
                "Look at the blue circles during calibration",
                "Press R to reset calibration",
                "Press ESC to exit"
            ]
            
            for i, instruction in enumerate(instructions):
                draw_text(display, instruction,
                         (20, display_height - 100 + (i * 30)))
        
        # Draw error message if any
        if error_message:
            draw_error_message(display, error_message)
            # Reset error after displaying
            error_counter = error_counter + 1 if 'error_counter' in locals() else 1
            if error_counter > 30:  # Clear error after ~1 second (30 frames)
                error_message = None
                error_counter = 0
        
        # Show the display
        cv2.imshow("Eye Tracking Calibration", display)
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            running = False
        elif key == 32 and not calibration_started:  # SPACE
            calibration_started = True
            print("Starting calibration...")
        elif key == ord('r') and calibration_started:  # R
            # Reset calibration
            iterator = 0
            prev_x, prev_y = 0, 0
            calibration_complete = False
            print("Calibration reset")
    
    except Exception as e:
        error_message = f"Error during eye tracking: {str(e)}"
        print(error_message)
        traceback.print_exc()

# Clean up
cap.release()
cv2.destroyAllWindows() 