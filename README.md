# Eye Tracking Color Blocks

This application demonstrates eye tracking technology by allowing users to interact with colored blocks on a web page using only their eyes.

## Features

- Four colored blocks (red, blue, green, yellow) that respond to eye gaze
- Real-time feedback about which color block you are looking at
- Calibration process to improve eye tracking accuracy
- Visual gaze tracking with heatmap-like visualization
- Simple web interface with status indicators

## Prerequisites

- Python 3.7 or higher
- Webcam
- Web browser (Chrome or Firefox recommended)

## Installation

1. Make sure you have all the required Python packages installed:

```bash
pip install -r requirements.txt
```

2. Ensure your webcam is properly connected and accessible to your computer.

## Usage

### Option 1: Run the main script (Recommended)

For the best experience with eye calibration:

```bash
python main.py
```

### Option 2: Run the web demo

To start the web-based eye tracking demo:

```bash
python eye_tracker/tracker.py
```

The application will open in your default web browser. If it doesn't, navigate to `http://localhost:8000`.

### Using the Application

1. Click the "Calibrate" button to start the calibration process. Follow the red dot with your eyes as it moves across the screen.

2. After calibration is complete, click "Start Eye Tracking" to begin tracking your eyes.

3. Look at the different colored blocks on the screen. The block you're looking at will be highlighted, and your gaze will be visualized on the screen.

4. To stop eye tracking, click the "Stop" button.

## Troubleshooting

- If the webcam cannot be accessed, try restarting the application or your computer.
- If eye tracking is not accurate, try the calibration process again in good lighting conditions.
- Make sure your face is clearly visible to the webcam and you're at a comfortable distance (approximately 50-70 cm).
- If the application fails to start, check the console for error messages.

## Project Structure

- `eyegestures/` - Core eye tracking library that handles eye tracking and calibration
- `eye_tracker/` - Contains the Python code for the web-based demo
  - `tracker.py` - Main script for handling eye tracking and the web server
- `web/` - Contains the web interface files
  - `index.html` - Main HTML file
  - `css/style.css` - CSS styles for the web interface
  - `js/main.js` - JavaScript code for handling eye tracking interaction
- `main.py` - Primary entry point for the full eye tracking application

## License

This project is licensed under the MIT License - see the LICENSE file for details. 