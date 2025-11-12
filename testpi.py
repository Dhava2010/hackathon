# camera_stream.py
from flask import Flask, Response
from picamera2 import Picamera2
import threading
import time

app = Flask(__name__)

# Global variable to hold the latest frame
latest_frame = None
frame_lock = threading.Lock()

def capture_frames():
    global latest_frame
    picam2 = Picamera2()
    config = picam2.create_video_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    print("Camera started...")

    while True:
        frame = picam2.capture_array()
        # Encode as JPEG
        _, jpeg = picam2.encode_jpeg(frame)
        with frame_lock:
            latest_frame = jpeg
        time.sleep(0.03)  # ~30 FPS

@app.route('/')
def index():
    return '''
    <html>
        <body>
            <h1>Raspberry Pi Camera Stream</h1>
            <img src="/video_feed" width="640" height="480"/>
        </body>
    </html>
    '''

@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            with frame_lock:
                if latest_frame is None:
                    continue
                frame = latest_frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.03)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Start frame capture in background
    threading.Thread(target=capture_frames, daemon=True).start()
    # Give camera time to initialize
    time.sleep(2)
    app.run(host='0.0.0.0', port=5000, threaded=True)
