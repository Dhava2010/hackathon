from flask import Flask, Response
import cv2

app = Flask(__name__)

# Open USB camera (usually /dev/video0)
camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # Yield frame in HTTP multipart stream
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
    # Host on all interfaces (so you can access it via Pi's IP)
    app.run(host='0.0.0.0', port=8080, debug=False)
