# main.py
# Updated to address camera reading issues:
# - Use CAP_V4L2 backend explicitly.
# - Set FOURCC to MJPG for better compatibility with USB webcams.
# - Set a reasonable resolution.
# - Add a short delay and initial reads to warm up the camera.
# - Loop with timeout for initial frame read.

import cv2
import numpy as np
import time
import socket
from detection import detect_targets
from crossing import check_crossing
from firing import init_servo, fire_gun

# Initialize video capture with V4L2 backend
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Set codec to MJPG for USB cameras
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
# Set resolution (adjust if needed based on camera capabilities)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Warm up the camera
time.sleep(2)
for _ in range(10):
    cap.read()

# Attempt to read initial frame with timeout
start_time = time.time()
while time.time() - start_time < 10:
    ret, frame = cap.read()
    if ret:
        break
    time.sleep(0.1)
else:
    print("Error: Timeout waiting for initial frame.")
    cap.release()
    exit()

if not ret:
    print("Error: Could not read initial frame.")
    cap.release()
    exit()

height, width, _ = frame.shape

# Mental line position (adjust based on gun aiming, e.g., bottom left/right)
# Assuming aiming at bottom right; set to a value where targets cross
line_x = width * 3 // 4  # Example: towards the right; tweak as needed

# Initialize servo
servo = init_servo(18)

# Cooldown tracking
last_fire_time = 0
cooldown = 3  # seconds

# Previous targets for crossing check
previous_targets = []

# Set up socket server for streaming to PC
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 5000))  # Listen on all interfaces, port 5000
server.listen(1)
server.settimeout(0.1)  # Non-blocking accept
conn = None

print("Starting main loop. Connect viewer from PC to port 5000.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Warning: Failed to read frame. Skipping.")
        continue

    # Detect targets
    current_targets = detect_targets(frame)

    # Draw bounding boxes and mental line on a copy for visualization
    vis_frame = frame.copy()
    for (x, y, w, h) in current_targets:
        cv2.rectangle(vis_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.line(vis_frame, (line_x, 0), (line_x, height), (0, 0, 255), 2)

    # Check for crossings if cooldown is over
    current_time = time.time()
    if current_time - last_fire_time > cooldown:
        if check_crossing(current_targets, previous_targets, line_x):
            fire_gun(servo)
            last_fire_time = current_time
            print("Fired!")

    # Update previous targets
    previous_targets = current_targets

    # Handle socket connection and send frame if connected
    if conn is None:
        try:
            conn, addr = server.accept()
            print(f"Viewer connected from {addr}")
        except socket.timeout:
            pass
    if conn:
        try:
            _, jpg = cv2.imencode('.jpg', vis_frame)
            size = len(jpg)
            conn.sendall(size.to_bytes(4, 'big') + jpg.tobytes())
        except BrokenPipeError:
            print("Viewer disconnected.")
            conn = None

    # Small delay to control frame rate
    time.sleep(0.03)  # ~30 fps

# Cleanup
cap.release()
if conn:
    conn.close()
server.close()
