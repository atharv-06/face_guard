from flask import Flask, render_template, Response, redirect, url_for
import sqlite3, os
from camera import VideoCamera, DB_PATH, ensure_db
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)  # Initialize SocketIO for real-time events
ensure_db()

camera = None

def get_camera():
    global camera
    if camera is None:
        camera = VideoCamera(cam_index=0)
    return camera

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    cam = get_camera()
    # Pass socketio to generator so it can emit face detection events
    return Response(cam.generator(socketio=socketio),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/logs')
def logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, confidence, timestamp FROM logs ORDER BY id DESC LIMIT 200")
    rows = c.fetchall()
    conn.close()
    return render_template('logs.html', logs=rows)

@app.route('/manage')
def manage():
    dataset_path = "dataset"
    persons = []
    if os.path.exists(dataset_path):
        persons = sorted([d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))])
    return render_template('manage.html', persons=persons)

@app.route('/refresh_labels')
def refresh_labels():
    cam = get_camera()
    cam.refresh_label_map()
    return redirect(url_for('manage'))

if __name__ == "__main__":
    # Run with socketio for real-time notifications
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
