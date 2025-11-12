

import cv2
import numpy as np

def detect_targets(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_green = np.array([40, 50, 50])
    upper_green = np.array([80, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    mask = cv2.medianBlur(mask, 5)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    targets = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 100:
            continue
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue
        circularity = 4 * np.pi * area / (perimeter ** 2)
        if circularity > 0.7:  # Threshold for circular shapes
            x, y, w, h = cv2.boundingRect(cnt)
            targets.append((x, y, w, h))
    return targets
