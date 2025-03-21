import math
import numpy as np
from eyeGestures.screenTracker.dataPoints import ScreenROI

class Heatmap:
    """Class for generating and analyzing heatmaps of gaze data."""

    def __init__(self, width, height, points):
        """Initialize a heatmap with dimensions and points."""
        self.width = width
        self.height = height
        self.points = points
        self.roi = self._calculate_roi()
    
    def _calculate_roi(self):
        """Calculate a region of interest based on the points."""
        if not self.points or len(self.points) < 2:
            # Return a default ROI if not enough points
            default_x = self.width // 4
            default_y = self.height // 4
            default_w = self.width // 2
            default_h = self.height // 2
            return ScreenROI(default_x, default_y, default_w, default_h)
        
        try:
            # Convert points to numpy array
            X = np.array(self.points)
            
            # Calculate center of mass
            center_x = np.mean(X[:, 0])
            center_y = np.mean(X[:, 1])
            
            # Calculate standard deviation for width and height
            std_x = np.std(X[:, 0])
            std_y = np.std(X[:, 1])
            
            # Set ROI based on center and standard deviations
            # Use at least 10% of screen size or 2x standard deviation, whichever is larger
            roi_width = max(self.width * 0.1, std_x * 2)
            roi_height = max(self.height * 0.1, std_y * 2)
            
            # Ensure the ROI is within screen bounds
            x = max(0, center_x - roi_width / 2)
            y = max(0, center_y - roi_height / 2)
            
            # Create and return the ROI
            return ScreenROI(x, y, roi_width, roi_height)
            
        except Exception as e:
            print(f"Error calculating heatmap ROI: {e}")
            # Return a default ROI on error
            default_x = self.width // 4
            default_y = self.height // 4
            default_w = self.width // 2
            default_h = self.height // 2
            return ScreenROI(default_x, default_y, default_w, default_h)
    
    def getBoundaries(self):
        """Get the boundaries of the ROI."""
        return self.roi.getBoundaries()
    
    def getCenter(self):
        """Get the center point of the ROI."""
        x, y, width, height = self.roi.getBoundaries()
        return (x + width / 2, y + height / 2) 