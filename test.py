# test_camera.py
# Run this on the Raspberry Pi to test if the camera works

import cv2

# Try to open the USB camera
cap = cv2.VideoCapture(0)  # 0 = /dev/video0

# Force MJPG format (most USB cameras support this)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Opening camera... (Press ESC to quit)")

# Give camera time to start
import time
time.sleep(2)

while True:
    ret, frame = cap.read()
    if not ret:
        print("ERROR: Can't read frame. Camera not working?")
        break

    # Show the frame
    cv2.imshow('USB Camera Test - Press ESC to Exit', frame)

    # Press ESC to quit
    if cv2.waitKey(1) == 27:
        print("ESC pressed. Closing.")
        break

cap.release()
cv2.destroyAllWindows()
print("Camera test finished.")
