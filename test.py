

import cv2


cap = cv2.VideoCapture(0) 

cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Opening camera... (Press ESC to quit)")

import time
time.sleep(2)

while True:
    ret, frame = cap.read()
    if not ret:
        print("ERROR: Can't read frame. Camera not working?")
        break

    cv2.imshow('USB Camera Test - Press ESC to Exit', frame)


    if cv2.waitKey(1) == 27:
        print("ESC pressed. Closing.")
        break

cap.release()
cv2.destroyAllWindows()
print("Camera test finished.")
