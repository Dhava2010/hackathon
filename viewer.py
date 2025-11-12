# viewer.py
# This script runs on your PC (not the Raspberry Pi).
# It connects to the Raspberry Pi's socket server and displays the streamed frames with bounding boxes and mental line.
# No calculations are done here; it's just for viewing.
# Replace 'pi_ip' with the actual IP address of your Raspberry Pi.

import socket
import cv2
import numpy as np

pi_ip = '192.168.1.100'  # REPLACE with your Raspberry Pi's IP address
port = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((pi_ip, port))
print("Connected to Raspberry Pi. Press ESC to exit.")

while True:
    # Receive size
    size_data = sock.recv(4)
    if not size_data:
        break
    size = int.from_bytes(size_data, 'big')

    # Receive image data
    data = b''
    while len(data) < size:
        packet = sock.recv(size - len(data))
        if not packet:
            break
        data += packet

    # Decode and display
    img_array = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if img is not None:
        cv2.imshow('Raspberry Pi Camera View', img)

    key = cv2.waitKey(1)
    if key == 27:  # ESC to exit
        break

sock.close()
cv2.destroyAllWindows()
print("Viewer closed.")
