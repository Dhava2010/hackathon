
import cv2
import numpy as np
import time
import socket
import os


os.system("sudo lsof /dev/video0 2>/dev/null | grep video0 | awk '{print $2}' | xargs -r sudo kill -9 2>/dev/null")
print("Camera freed from other processes")

from detection import detect_targets
from crossing import check_crossing
from firing import init_servo, fire_gun


def open_camera():
    cap = cv2.VideoCapture(0)  
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) 

    print("Opening camera... (2s warm-up)")
    time.sleep(2)

    # Flush stale frames
    for _ in range(10):
        cap.grab()
        time.sleep(0.05)

    return cap

cap = open_camera()


def get_first_frame():
    print("Waiting for first frame...")
    for i in range(50):
        ret, frame = cap.read()
        if ret and frame is not None:
            return frame
        print(f"  Trying... ({i+1}/50)")
        time.sleep(0.1)
    raise RuntimeError("Camera not streaming. Check power/cable.")

frame = get_first_frame()
h, w = frame.shape[:2]
print(f"CAMERA READY → {w}×{h}")

line_x = int(w * 0.75)
servo = init_servo(18)
COOLDOWN = 3.0
last_fire = 0.0
prev_targets = []

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', 5000))
server.listen(1)
server.settimeout(0.1)
conn = None
print("Streaming on port 5000")


while True:
    ret, frame = cap.read()
    if not ret:
        time.sleep(0.01)
        continue

    targets = detect_targets(frame)
    vis = frame.copy()
    for (x, y, w, h) in targets:
        cv2.rectangle(vis, (x, y), (x+w, y+h), (0,255,0), 2)
    cv2.line(vis, (line_x, 0), (line_x, h), (0,0,255), 2)

    now = time.time()
    if now - last_fire > COOLDOWN:
        if check_crossing(targets, prev_targets, line_x):
            fire_gun(servo)
            last_fire = now
            print("FIRE!")

    prev_targets = targets

    if conn is None:
        try:
            conn, addr = server.accept()
            print(f"Viewer connected: {addr}")
        except:
            pass
    if conn:
        try:
            _, jpg = cv2.imencode('.jpg', vis, [cv2.IMWRITE_JPEG_QUALITY, 80])
            data = jpg.tobytes()
            conn.sendall(len(data).to_bytes(4, 'big') + data)
        except:
            conn.close()
            conn = None

    time.sleep(0.03)

cap.release()
if conn: conn.close()
server.close()
