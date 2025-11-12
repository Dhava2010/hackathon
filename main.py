# main.py  (run on the Raspberry Pi)
# Updated to match EXACTLY the working test_camera.py init
# - No CAP_V4L2 (since it worked without)
# - Added extra warm-up grabs to flush any bad buffers
# - Increased first-frame timeout to 30s with more retries
# - If still fails, print debug info

import cv2
import numpy as np
import time
import socket
from detection import detect_targets
from crossing import check_crossing
from firing import init_servo, fire_gun

# -------------------------------------------------
#  CAMERA: EXACTLY LIKE YOUR WORKING test_camera.py
# -------------------------------------------------
def open_camera():
    cap = cv2.VideoCapture(0)  # NO CAP_V4L2 – worked in test
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Opening camera... (2-second warm-up)")
    time.sleep(2)

    # Extra: Grab 10 times to warm up and flush buffers
    for _ in range(10):
        cap.grab()  # Grab without decode to prime the pump

    return cap

# -------------------------------------------------
#  OPEN CAMERA
# -------------------------------------------------
cap = open_camera()

# -------------------------------------------------
#  READ FIRST FRAME (longer timeout + debug)
# -------------------------------------------------
def read_first_frame(timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        ret, frame = cap.read()
        if ret and frame is not None and frame.size > 0:
            return frame
        print(f"Retry read... ({int(timeout - (time.time() - start))}s left)")
        time.sleep(0.2)  # Longer sleep for USB settle
    # Debug if fail
    print("DEBUG: Camera opened? ", cap.isOpened())
    print("DEBUG: Get WIDTH: ", cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    print("DEBUG: Get FOURCC: ", cap.get(cv2.CAP_PROP_FOURCC))
    raise RuntimeError("Timeout – camera accessed (LED green) but no frames. See fixes below.")

print("Waiting for first frame...")
frame = read_first_frame()
height, width = frame.shape[:2]
print(f"CAMERA OK → {width}×{height}")

# -------------------------------------------------
#  MENTAL LINE
# -------------------------------------------------
line_x = int(width * 0.75)  # adjust if needed
print(f"Mental line at x = {line_x}")

# -------------------------------------------------
#  SERVO
# -------------------------------------------------
servo = init_servo(18)

# -------------------------------------------------
#  COOLDOWN & STATE
# -------------------------------------------------
COOLDOWN = 3.0
last_fire = 0.0
prev_targets = []

# -------------------------------------------------
#  STREAMING SERVER
# -------------------------------------------------
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', 5000))
server.listen(1)
server.settimeout(0.1)
conn = None
print("Streaming server ready – run viewer.py on PC")

# -------------------------------------------------
#  MAIN LOOP
# -------------------------------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        print("Dropped frame – retrying...")
        time.sleep(0.01)
        continue

    # Detection
    cur_targets = detect_targets(frame)

    # Visualisation
    vis = frame.copy()
    for (x, y, w, h) in cur_targets:
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.line(vis, (line_x, 0), (line_x, height), (0, 0, 255), 2)

    # Crossing + Fire
    now = time.time()
    if now - last_fire > COOLDOWN:
        if check_crossing(cur_targets, prev_targets, line_x):
            fire_gun(servo)
            last_fire = now
            print("FIRE!")

    prev_targets = cur_targets

    # Streaming
    if conn is None:
        try:
            conn, addr = server.accept()
            print(f"Viewer connected: {addr}")
        except socket.timeout:
            pass
    if conn:
        try:
            _, jpg = cv2.imencode('.jpg', vis, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if jpg.size == 0:
                continue
            data = jpg.tobytes()
            conn.sendall(len(data).to_bytes(4, 'big') + data)
        except BrokenPipeError:
            print("Viewer disconnected.")
            conn.close()
            conn = None

    time.sleep(0.03)  # ~30 fps

# -------------------------------------------------
#  CLEANUP
# -------------------------------------------------
cap.release()
if conn:
    conn.close()
server.close()
