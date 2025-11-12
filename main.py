# main.py  (run on the Raspberry Pi)
import cv2
import numpy as np
import time
import socket
from detection import detect_targets
from crossing import check_crossing
from firing import init_servo, fire_gun

# -------------------------------------------------
#  CAMERA: FORCE V4L2 + MJPG + RESOLUTION (same as test_camera.py)
# -------------------------------------------------
def open_camera():
    # FORCE V4L2 backend – this eliminates GStreamer warnings
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

    # Set format and resolution
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Reduce buffer size to prevent select() timeout
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print("Opening camera with V4L2 + MJPG... (2-second warm-up)")
    time.sleep(2)
    return cap

# -------------------------------------------------
#  OPEN CAMERA
# -------------------------------------------------
cap = open_camera()

# -------------------------------------------------
#  READ FIRST FRAME (with timeout + retry)
# -------------------------------------------------
def read_first_frame(timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        ret, frame = cap.read()
        if ret and frame is not None:
            return frame
        print("Waiting for first frame... (retry 5s left)" if (time.time() - start) < 5 else "Still waiting...")
        time.sleep(0.1)
    raise RuntimeError("Timeout – camera not delivering frames")

print("Waiting for first frame...")
frame = read_first_frame()
height, width = frame.shape[:2]
print(f"CAMERA OK → {width}×{height}")

# -------------------------------------------------
#  MENTAL LINE
# -------------------------------------------------
line_x = int(width * 0.75)  # adjust if gun hits left/right
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
