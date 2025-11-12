# camera_stream_opencv.py
from flask import Flask, Response
import cv2
import threading
import time

app = Flask(__name__)

# Global latest frame + lock
latest_frame = None
frame_lock = threading.Lock()

def capture_loop():
    global latest_frame

    # --- Open the Raspberry Pi camera using GStreamer ---
    # Works on Raspberry Pi OS Bookworm+ (libcamera)
    pipeline = (
        "libcamerasrc ! "
        "video/x-raw, width=640, height=480, framerate=30/1 ! "
        "videoconvert ! appsink"
    )
    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

    if not cap.isOpened():
        print("ERROR: Cannot open camera!")
        return

    print("Camera opened – streaming started")
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        # Encode as JPEG
        _, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        with frame_lock:
            latest_frame = jpeg.tobytes()

        time.sleep(0.03)   # ~30 FPS

    cap.release()


@app.route('/')
def index():
    return '''
    <html><body>
        <h1>Raspberry Pi OpenCV Stream</h1>
        <img src="/video_feed" width="640" height="480"/>
    </body></html>
    '''


@app.route('/video_feed')
def video_feed():
    def gen():
        while True:
            with frame_lock:
                if latest_frame is None:
                    continue
                frame = latest_frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.03)
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    # Start capture in background
    threading.Thread(target=capture_loop, daemon=True).start()
    time.sleep(2)                 # give camera time to init
    app.run(host='0.0.0.0', port=9999, threaded=True)
