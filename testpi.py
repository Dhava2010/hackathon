from flask import Flask, Response
import cv2
import time

app = Flask(__name__)

camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FPS, 5)

def generate_frames():
    fps_limit = 5
    frame_time = 1.0 / fps_limit
    last_frame_time = 0

    while True:
        success, frame = camera.read()
        if not success:
            break
        
        now = time.time()
        if now - last_frame_time < frame_time:
            time.sleep(frame_time - (now - last_frame_time))
        
        last_frame_time = time.time()

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '<h1>Raspberry Pi Camera Stream</h1><img src="/video" width="640" />'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)

can you downscale the resolution? to like 360p or ike 240p? whatever best for performenace
