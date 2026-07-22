import cv2
import numpy as np
import os

def analyze_growth(mode):
    photo_path = "live_mushrooms.jpg"
    # Capture an image from the webcam
    exit_code = os.system(f"fswebcam -d /dev/video0 -r 640x480 --no-banner {photo_path}")
    
    if exit_code != 0:
        return None

    img = cv2.imread(photo_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Select HSV thresholds depending on the active mode
    if "Mushrooms" in mode:
        # Detect white mushroom caps
        lower = np.array([0, 0, 160])
        upper = np.array([180, 40, 255])
    else: 
        # Detect green plant areas for basil, microgreens, and strawberries
        lower = np.array([35, 40, 40])
        upper = np.array([85, 255, 255])

    mask = cv2.inRange(hsv, lower, upper)
    white_pixels = cv2.countNonZero(mask)
    total_pixels = mask.shape[0] * mask.shape[1]
    
    return round((white_pixels / total_pixels) * 100, 2)