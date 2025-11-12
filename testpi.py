# pi_stream_server.py
import cv2
import socket
import struct
import pickle

# Open Pi camera
pipeline = (
    "libcamerasrc ! "
    "video/x-raw,width=640,height=480,framerate=30/1 ! "
    "videoconvert ! appsink"
)
cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
if not cap.isOpened():
    print("ERROR: Cannot open camera!")
    exit(1)

# Create TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 8485))  # listen on port 8485
server_socket.listen(1)
print("📸 Waiting for connection on port 8485...")

conn, addr = server_socket.accept()
print(f"✅ Connected to {addr}")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Encode frame as JPEG to save bandwidth
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

        # Serialize using pickle
        data = pickle.dumps(buffer)

        # Pack message length before data
        message_size = struct.pack(">L", len(data))
        conn.sendall(message_size + data)
except Exception as e:
    print("❌ Stream stopped:", e)
finally:
    conn.close()
    server_socket.close()
    cap.release()
