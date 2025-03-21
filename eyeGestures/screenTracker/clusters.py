import math
import numpy as np
from sklearn.cluster import DBSCAN
from eyeGestures.screenTracker.dataPoints import ScreenROI

class Clusters:
    """Class for clustering gaze data points and finding main clusters."""

    def __init__(self, points):
        """Initialize the clusters with a set of points."""
        self.points = points
        self.eps = 100  # Default clustering distance
        self.min_samples = 5  # Minimum samples for a cluster
        self.cluster = None
        
        if len(points) > self.min_samples:
            self._process_clusters()
    
    def _process_clusters(self):
        """Process the points to find clusters."""
        if not self.points or len(self.points) < self.min_samples:
            return None
        
        try:
            # Convert points to numpy array
            X = np.array(self.points)
            
            # Use DBSCAN for clustering
            clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(X)
            
            # Get labels
            labels = clustering.labels_
            
            # Find the largest cluster
            unique_labels = set(labels)
            max_size = 0
            max_label = -1
            
            for label in unique_labels:
                if label == -1:  # Skip noise points
                    continue
                
                cluster_size = np.sum(labels == label)
                if cluster_size > max_size:
                    max_size = cluster_size
                    max_label = label
            
            if max_label != -1:
                # Get points in the largest cluster
                cluster_points = X[labels == max_label]
                
                # Calculate bounding box
                min_x = np.min(cluster_points[:, 0])
                min_y = np.min(cluster_points[:, 1])
                max_x = np.max(cluster_points[:, 0])
                max_y = np.max(cluster_points[:, 1])
                
                # Create a ScreenROI for the main cluster
                width = max_x - min_x
                height = max_y - min_y
                self.cluster = ScreenROI(min_x, min_y, width, height)
        
        except Exception as e:
            print(f"Error clustering points: {e}")
            return None
    
    def getMainCluster(self):
        """Get the main (largest) cluster as a ScreenROI."""
        return self.cluster 