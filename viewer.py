

import socket
import cv2
import numpy as np

pi_ip = '192.168.1.14' 
port = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((pi_ip, port))
print("Connected to Raspberry Pi. Press ESC to exit.")

while True:
    size_data = sock.recv(4)
    if not size_data:
        break
    size = int.from_bytes(size_data, 'big')


    data = b''
    while len(data) < size:
        packet = sock.recv(size - len(data))
        if not packet:
            break
        data += packet


    img_array = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if img is not None:
        cv2.imshow('Raspberry Pi Camera View', img)

    key = cv2.waitKey(1)
    if key == 27: 
        break

sock.close()
cv2.destroyAllWindows()
print("Viewer closed.")
