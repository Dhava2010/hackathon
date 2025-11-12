# main.py  (run on the Raspberry Pi)
# -------------------------------------------------
#  CAMERA INITIALISATION – COPY-PASTE FROM YOUR WORKING test_camera.py
# -------------------------------------------------
import cv2
import numpy as np
import time
import socket
from detection import detect_targets
from crossing import check_crossing
from firing import init_servo, fire_gun

def open_camera():
    cap = cv2.VideoCapture(0)                     # same as test_camera.py
    cap.set(cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))   # force MJPG
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Opening camera... (2-second warm-up)")
    time.sleep(2)                                 # same warm-up
    return cap

# -------------------------------------------------
#  OPEN CAMERA + FIRST FRAME (with timeout)
# -------------------------------------------------
cap = open_camera()
def read_first_frame(timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        ret, frame = cap.read()
        if ret:
            return frame
        time.sleep(0.05)
    raise RuntimeError("Timeout – no frame from camera")
frame = read_first_frame()
height, width = frame.shape[:2]
print(f"Camera OK → {width}×{height}")

# -------------------------------------------------
#  MENTAL LINE (adjust to where the gun actually hits)
# -------------------------------------------------
line_x = int(width * 0.75)          # 75 % of the width – change if needed
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
#  STREAMING SERVER (same port 5000)
# -------------------------------------------------
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', 5000))
server.listen(1)
server.settimeout(0.1)
conn = None
print("Streaming server ready – run viewer.py on your PC")

# -------------------------------------------------
#  MAIN LOOP
# -------------------------------------------------
while True:
    ret, frame = cap.read()
    if not ret:                                 # dropped frame → retry
        print("Warning: dropped frame – trying again")
        time.sleep(0.01)
        continue

    # ---- detection -------------------------------------------------
    cur_targets = detect_targets(frame)

    # ---- visualisation ---------------------------------------------
    vis = frame.copy()
    for (x, y, w, h) in cur_targets:
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.line(vis, (line_x, 0), (line_x, height), (0, 0, 255), 2)

    # ---- crossing logic --------------------------------------------
    now = time.time()
    if now - last_fire > COOLDOWN:
        if check_crossing(cur_targets, prev_targets, line_x):
            fire_gun(servo)
            last_fire = now
            print("FIRE!")

    prev_targets = cur_targets

    # ---- streaming --------------------------------------------------
    if conn is None:
        try:
            conn, addr = server.accept()
            print(f"Viewer connected: {addr}")
        except socket.timeout:
            pass
    if conn:
        try:
            _, jpg = cv2.imencode('.jpg', vis,
                                 [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if jpg.size == 0:
                print("Warning: JPEG encode failed")
                continue
            data = jpg.tobytes()
            conn.sendall(len(data).to_bytes(4, 'big') + data)
        except BrokenPipeError:
            print("Viewer disconnected.")
            conn.close()
            conn = None
        except Exception as e:
            print(f"Streaming error: {e}")
            conn.close()
            conn = None

    time.sleep(0.03)   # ~30 fps

# -------------------------------------------------
#  CLEANUP
# -------------------------------------------------
cap.release()
if conn:
    conn.close()
server.close()
