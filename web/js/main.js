// Global variables
let trackingActive = false;
let calibrationActive = false;
let currentColor = "None";
let gazePoints = []; // Store recent gaze points for visualization
const maxGazePoints = 30; // Maximum number of points to store for heatmap effect

// DOM elements
const startButton = document.getElementById('start-tracking');
const calibrateButton = document.getElementById('calibrate');
const stopButton = document.getElementById('stop-tracking');
const statusMessage = document.getElementById('status-message');
const currentBlockDisplay = document.getElementById('current-block');
const colorBlocks = document.querySelectorAll('.color-block');

// Initialize the UI
document.addEventListener('DOMContentLoaded', () => {
    // Set up button event listeners
    startButton.addEventListener('click', startTracking);
    calibrateButton.addEventListener('click', startCalibration);
    stopButton.addEventListener('click', stopTracking);
    
    // Initially disable stop button
    stopButton.disabled = true;
    
    // Create gaze visualization layer
    createGazeVisualization();
    
    // Update status message
    updateStatus("Ready to start eye tracking");
    
    // Add hover effect to color blocks for testing
    colorBlocks.forEach(block => {
        block.addEventListener('mouseenter', () => {
            highlightBlock(block.id);
        });
        
        block.addEventListener('mouseleave', () => {
            if (currentColor !== block.id) {
                resetHighlight(block.id);
            }
        });
    });
});

// Create gaze visualization layer
function createGazeVisualization() {
    // Add styles for gaze visualization
    const style = document.createElement('style');
    style.id = 'gaze-visualization-style';
    style.textContent = `
        #gaze-layer {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            pointer-events: none;
            z-index: 9998;
        }
        .gaze-point {
            position: absolute;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-left: -5px;
            margin-top: -5px;
            background-color: rgba(255, 0, 0, 0.7);
            opacity: 0.7;
            transition: opacity 0.5s ease;
        }
        .current-gaze {
            width: 20px;
            height: 20px;
            margin-left: -10px;
            margin-top: -10px;
            background-color: rgba(255, 0, 0, 0.8);
            box-shadow: 0 0 10px 2px rgba(255, 0, 0, 0.5);
            z-index: 9999;
            opacity: 1;
        }
    `;
    document.head.appendChild(style);
    
    // Create gaze layer
    const gazeLayer = document.createElement('div');
    gazeLayer.id = 'gaze-layer';
    document.body.appendChild(gazeLayer);
}

// Update gaze visualization with new point
function updateGazeVisualization(x, y) {
    const gazeLayer = document.getElementById('gaze-layer');
    if (!gazeLayer) return;
    
    // Create new point
    const point = document.createElement('div');
    point.className = 'gaze-point current-gaze';
    point.style.left = `${x}px`;
    point.style.top = `${y}px`;
    gazeLayer.appendChild(point);
    
    // Add to tracking array
    gazePoints.push({ element: point, timestamp: Date.now() });
    
    // Remove current-gaze class after a short delay
    setTimeout(() => {
        point.className = 'gaze-point';
    }, 100);
    
    // Clean up old points
    if (gazePoints.length > maxGazePoints) {
        const oldPoint = gazePoints.shift();
        if (oldPoint.element && oldPoint.element.parentNode) {
            oldPoint.element.parentNode.removeChild(oldPoint.element);
        }
    }
    
    // Fade out older points
    gazePoints.forEach((p, index) => {
        const age = Date.now() - p.timestamp;
        if (age > 2000) { // Points older than 2 seconds
            if (p.element && p.element.parentNode) {
                p.element.parentNode.removeChild(p.element);
                gazePoints.splice(index, 1);
            }
        } else {
            // Adjust opacity based on age
            const opacity = Math.max(0.1, 1 - (age / 2000));
            p.element.style.opacity = opacity;
        }
    });
}

// Convert gaze coordinates from screen space to page space
function convertGazeCoordinates(screenX, screenY) {
    // Get the current browser window dimensions
    const browserWidth = window.innerWidth;
    const browserHeight = window.innerHeight;
    
    // Get window position (estimate based on typical browser chrome)
    // These values should be adjusted based on testing
    const windowOffsetX = screen.width * 0.05; // Estimate window left position is 5% from screen left
    const windowOffsetY = screen.height * 0.08; // Estimate window top position is 8% from screen top
    
    // Calculate relative position within screen
    const screenRelX = (screenX - windowOffsetX) / (screen.width * 0.9); // Assuming browser width is ~90% of screen
    const screenRelY = (screenY - windowOffsetY) / (screen.height * 0.84); // Assuming browser height is ~84% of screen
    
    // Convert to browser coordinates
    const browserX = screenRelX * browserWidth;
    const browserY = screenRelY * browserHeight;
    
    // Log for debugging
    console.log(`Screen: (${screenX}, ${screenY}), Browser: (${browserX}, ${browserY})`);
    console.log(`Screen dimensions: ${screen.width}x${screen.height}, Browser: ${browserWidth}x${browserHeight}`);
    
    return { 
        x: Math.max(0, Math.min(browserWidth, browserX)), 
        y: Math.max(0, Math.min(browserHeight, browserY)) 
    };
}

// Start eye tracking
function startTracking() {
    if (trackingActive) return;
    
    updateStatus("Starting eye tracking...");
    
    // Make API call to start tracking
    fetch('/api/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    })
    .then(response => {
        console.log("Response from /api/start:", response);
        return response.json();
    })
    .then(data => {
        console.log("Start tracking response:", data);
        if (data.status === "started" || data.status === "already_running") {
            trackingActive = true;
            updateStatus("Eye tracking active");
            startButton.disabled = true;
            stopButton.disabled = false;
            
            // Clear old gaze points
            clearGazePoints();
            
            // Start polling for eye tracking data
            startPolling();
        } else {
            updateStatus("Failed to start eye tracking");
        }
    })
    .catch(error => {
        console.error('Error starting tracking:', error);
        updateStatus("Error: Could not start eye tracking");
    });
}

// Clear all gaze points
function clearGazePoints() {
    const gazeLayer = document.getElementById('gaze-layer');
    if (gazeLayer) {
        gazeLayer.innerHTML = '';
    }
    gazePoints = [];
}

// Start calibration
function startCalibration() {
    updateStatus("Starting calibration...");
    
    // Make API call to start calibration
    fetch('/api/calibrate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "calibration_started") {
            calibrationActive = true;
            updateStatus("Calibration in progress - look at each dot that appears");
            startButton.disabled = true;
            calibrateButton.disabled = true;
            stopButton.disabled = true;
            
            // Create calibration overlay
            createCalibrationOverlay();
            
            // Poll for calibration status
            checkCalibrationStatus();
        } else {
            updateStatus("Failed to start calibration");
        }
    })
    .catch(error => {
        console.error('Error starting calibration:', error);
        updateStatus("Error: Could not start calibration");
    });
}

// Stop eye tracking
function stopTracking() {
    if (!trackingActive) return;
    
    updateStatus("Stopping eye tracking...");
    
    // Make API call to stop tracking
    fetch('/api/stop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "stopped") {
            trackingActive = false;
            updateStatus("Eye tracking stopped");
            startButton.disabled = false;
            stopButton.disabled = true;
            
            // Reset all blocks
            resetAllBlocks();
        } else {
            updateStatus("Failed to stop eye tracking");
        }
    })
    .catch(error => {
        console.error('Error stopping tracking:', error);
        updateStatus("Error: Could not stop eye tracking");
    });
}

// Poll for eye tracking data
let pollingInterval = null;
function startPolling() {
    // Clear any existing interval
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    // Reset error counter
    errorCount = 0;
    
    // Start new polling interval
    pollingInterval = setInterval(pollEyeTrackerStatus, 50); // Poll every 50ms for smoother visualization
}

// Create calibration overlay with dots
function createCalibrationOverlay() {
    // Create overlay container
    const overlay = document.createElement('div');
    overlay.id = 'calibration-overlay';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    overlay.style.backgroundColor = 'rgba(8, 24, 58, 0.85)';  // Dark blue background
    overlay.style.zIndex = '9999';
    overlay.style.display = 'flex';
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';
    overlay.style.flexDirection = 'column';
    
    // Add instruction text
    const instructions = document.createElement('div');
    instructions.textContent = 'Follow the red dot with your eyes';
    instructions.style.color = 'white';
    instructions.style.fontSize = '28px';
    instructions.style.marginBottom = '20px';
    instructions.style.fontWeight = 'bold';
    instructions.style.textShadow = '0 2px 4px rgba(0,0,0,0.5)';
    overlay.appendChild(instructions);
    
    // Define calibration points (9-point calibration)
    const calibPoints = [
        {x: '10%', y: '10%'}, // Top left
        {x: '50%', y: '10%'}, // Top center
        {x: '90%', y: '10%'}, // Top right
        {x: '10%', y: '50%'}, // Middle left
        {x: '50%', y: '50%'}, // Center
        {x: '90%', y: '50%'}, // Middle right
        {x: '10%', y: '90%'}, // Bottom left
        {x: '50%', y: '90%'}, // Bottom center
        {x: '90%', y: '90%'}  // Bottom right
    ];
    
    // Create container for the dot (there will be only one)
    const dotContainer = document.createElement('div');
    dotContainer.id = 'dot-container';
    dotContainer.style.position = 'absolute';
    dotContainer.style.top = '0';
    dotContainer.style.left = '0';
    dotContainer.style.width = '100%';
    dotContainer.style.height = '100%';
    dotContainer.style.pointerEvents = 'none';
    overlay.appendChild(dotContainer);
    
    // Add to body
    document.body.appendChild(overlay);
    
    // Add animation style
    const style = document.createElement('style');
    style.id = 'calibration-style';
    style.textContent = `
        @keyframes pulse {
            0% { transform: scale(0.8); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); }
            50% { transform: scale(1.2); box-shadow: 0 0 0 10px rgba(255, 0, 0, 0); }
            100% { transform: scale(0.8); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); }
        }
        .calibration-dot {
            position: absolute;
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background-color: #ff3333;
            box-shadow: 0 0 10px 2px rgba(255,0,0,0.5), 0 0 20px 5px rgba(255,0,0,0.3);
            animation: pulse 1.5s infinite;
            transition: left 0.8s ease-in-out, top 0.8s ease-in-out;
            transform-origin: center center;
        }
    `;
    document.head.appendChild(style);
    
    // Create a single dot that will move between positions
    const dot = document.createElement('div');
    dot.className = 'calibration-dot';
    // Start position (off-screen)
    dot.style.left = '-50px';
    dot.style.top = '-50px';
    dotContainer.appendChild(dot);
    
    // Show calibration dots sequentially with smooth motion
    let currentPoint = 0;
    
    function moveToNextCalibrationPoint() {
        // If we've shown all points, clean up and return
        if (currentPoint >= calibPoints.length) {
            // Small delay before removing overlay to ensure the backend has completed
            setTimeout(() => {
                if (document.body.contains(overlay)) {
                    document.body.removeChild(overlay);
                    
                    // Force status update since sometimes the status check misses the end
                    calibrationActive = false;
                    updateStatus("Calibration complete");
                    startButton.disabled = false;
                    calibrateButton.disabled = false;
                    stopButton.disabled = !trackingActive;
                }
            }, 500);
            return;
        }
        
        // Move dot to next position with CSS transition
        dot.style.left = `calc(${calibPoints[currentPoint].x} - 13px)`;  // Center dot (half of 26px)
        dot.style.top = `calc(${calibPoints[currentPoint].y} - 13px)`;   // Center dot (half of 26px)
        
        // Increment point and schedule next move
        currentPoint++;
        setTimeout(moveToNextCalibrationPoint, 1800);  // 1.8 seconds per point
    }
    
    // Start with a small delay to let the overlay appear first
    setTimeout(moveToNextCalibrationPoint, 500);
}

// Poll for calibration status
function checkCalibrationStatus() {
    // Track the total time spent in calibration to avoid infinite waiting
    const startTime = Date.now();
    const maxCalibrationTime = 20000; // 20 seconds max for calibration
    
    const checkInterval = setInterval(() => {
        // Check if we've hit the maximum calibration time
        if (Date.now() - startTime > maxCalibrationTime) {
            clearInterval(checkInterval);
            calibrationActive = false;
            
            // Remove calibration overlay if it's still present
            const overlay = document.getElementById('calibration-overlay');
            if (overlay && document.body.contains(overlay)) {
                document.body.removeChild(overlay);
            }
            
            updateStatus("Calibration complete");
            startButton.disabled = false;
            calibrateButton.disabled = false;
            stopButton.disabled = !trackingActive;
            return;
        }
        
        fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            if (!data.calibration) {
                // Calibration is complete
                clearInterval(checkInterval);
                calibrationActive = false;
                
                // Remove calibration overlay if it's still present
                const overlay = document.getElementById('calibration-overlay');
                if (overlay && document.body.contains(overlay)) {
                    document.body.removeChild(overlay);
                }
                
                updateStatus("Calibration complete");
                startButton.disabled = false;
                calibrateButton.disabled = false;
                stopButton.disabled = !trackingActive;
            }
        })
        .catch(error => {
            console.error('Error checking calibration status:', error);
            clearInterval(checkInterval);
            calibrationActive = false;
            
            // Remove calibration overlay if it's still present
            const overlay = document.getElementById('calibration-overlay');
            if (overlay && document.body.contains(overlay)) {
                document.body.removeChild(overlay);
            }
            
            updateStatus("Error during calibration");
            startButton.disabled = false;
            calibrateButton.disabled = false;
            stopButton.disabled = !trackingActive;
        });
    }, 1000); // Check every second
}

// Poll eye tracker status
function pollEyeTrackerStatus() {
    if (!trackingActive) {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
        return;
    }
    
    fetch('/api/status')
    .then(response => response.json())
    .then(data => {
        // Debug status response
        console.log("Status data:", data);
        
        if (!data.tracking) {
            // Tracking has stopped on the server side
            trackingActive = false;
            updateStatus("Eye tracking stopped");
            startButton.disabled = false;
            stopButton.disabled = true;
            
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
            
            // Reset all blocks
            resetAllBlocks();
            return;
        }
        
        // Update gaze visualization
        if (data.gaze && data.gaze.x !== 0 && data.gaze.y !== 0) {
            // Only visualize when we have non-zero coordinates
            const pageCoords = convertGazeCoordinates(data.gaze.x, data.gaze.y);
            updateGazeVisualization(pageCoords.x, pageCoords.y);
        }
        
        // Update current color if it changed
        if (data.color !== currentColor) {
            // Reset previous color
            if (currentColor !== "None") {
                resetHighlight(currentColor.toLowerCase());
            }
            
            // Set new color
            currentColor = data.color;
            
            // Update display
            if (currentColor !== "None") {
                updateCurrentBlock(currentColor);
                highlightBlock(currentColor.toLowerCase());
            } else {
                updateCurrentBlock("None");
            }
        }
    })
    .catch(error => {
        console.error('Error polling eye tracker status:', error);
        
        // If there are multiple consecutive errors, stop polling
        if (pollingInterval) {
            errorCount++;
            if (errorCount > 5) {
                clearInterval(pollingInterval);
                pollingInterval = null;
                updateStatus("Connection to eye tracker lost");
                trackingActive = false;
                startButton.disabled = false;
                stopButton.disabled = true;
            }
        }
    });
}

// Update status message
function updateStatus(message) {
    statusMessage.textContent = message;
}

// Update current block display
function updateCurrentBlock(color) {
    currentBlockDisplay.textContent = color;
}

// Highlight a block
function highlightBlock(blockId) {
    const block = document.getElementById(blockId);
    if (block) {
        block.classList.add('looking');
    }
}

// Reset highlight on a block
function resetHighlight(blockId) {
    const block = document.getElementById(blockId);
    if (block) {
        block.classList.remove('looking');
    }
}

// Reset all blocks
function resetAllBlocks() {
    colorBlocks.forEach(block => {
        block.classList.remove('looking');
    });
    updateCurrentBlock("None");
    currentColor = "None";
}

// Error counter for tracking connection issues
let errorCount = 0;