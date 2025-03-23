# Eye Tracking Image Viewing System

This application demonstrates eye tracking technology by allowing users to view different categories of images while their gaze is tracked for analysis.

## Features

- Eye tracking calibration with visual feedback
- Multiple image categories (Beverages, Cars, Snacks) to explore
- Real-time gaze tracking visualization
- Data collection for eye tracking research
- Demo mode for testing without hardware

## Prerequisites

- Python 3.7 or higher
- Webcam (for hardware-based eye tracking)
- Web browser (Chrome or Firefox recommended)

## Installation

1. Make sure you have all the required Python packages installed:

```bash
pip install -r requirements.txt
```

2. For hardware-based tracking, ensure your webcam is properly connected and accessible to your computer.

## Usage

### Option 1: Run the main script with eye tracking hardware

For the full eye tracking experience with hardware support:

```bash
python main.py
```

This will run the local host version with complete eye tracking functionality, requiring a webcam and eye tracking hardware.

### Option 2: Run the integrated web application

To start the web-based eye tracking application with calibration:

```bash
python webapp/integrated_main.py
```

This version provides a web interface with eye tracking, calibration, and image viewing capabilities.

### Option 3: Run the simplified demo (no hardware required)

For testing the web application without eye tracking hardware:

```bash
python webapp/simplified_demo.py
```

This demo version simulates eye tracking and calibration, perfect for testing the interface without special hardware.

The applications will open in your default web browser. If they don't, navigate to `http://localhost:8080`.

### Using the Application

1. Select a category (Beverages, Cars, or Snacks) from the main interface.

2. You'll be redirected to the calibration page. Click "Start Calibration" to begin.

3. Follow the blue circles with the red dot in the center as they appear at different positions on the screen.

4. Once calibration is complete, click "Continue" to proceed to the image viewing interface.

5. The application will display images from your chosen category while tracking your gaze. A red dot indicates where the system thinks you're looking.

6. Results will be saved automatically for analysis.

## Troubleshooting

- If the webcam cannot be accessed, try restarting the application or your computer.
- If eye tracking is not accurate, try the calibration process again in good lighting conditions.
- Make sure your face is clearly visible to the webcam and you're at a comfortable distance (approximately 50-70 cm).
- If the application fails to start, check the console for error messages.
- For hardware issues, try the simplified demo mode which doesn't require eye tracking hardware.

## Project Structure

- `eyeGestures/` - Core eye tracking library that handles eye tracking and calibration
- `webapp/` - Contains the web application files
  - `calibration.html` - Calibration interface
  - `interface.html` - Main category selection interface
  - `simulator.html` - Image viewing interface with gaze tracking
  - `integrated_main.py` - Server script for the integrated application
  - `simplified_demo.py` - Server script for the hardware-free demo version
- `main.py` - Primary entry point for the full eye tracking application

## License

This project is licensed under the MIT License - see the LICENSE file for details. 