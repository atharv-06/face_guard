import cv2
import os
import numpy as np
from datetime import datetime, timedelta
import sqlite3
from threading import Lock
import requests

DB_PATH = "database/logs.db"
MODEL_PATH = "trained_model/lbph.yml"
HAAR_PATH = "haarcascade_frontalface_default.xml"
DATASET_DIR = "dataset"

db_lock = Lock()

# Ensure database exists
def ensure_db():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    confidence REAL,
                    timestamp TEXT
                )""")
    conn.commit()
    conn.close()
ensure_db()

class VideoCamera:
    def __init__(self, cam_index=0, scale_factor=1.3, min_neighbors=5, alert_cooldown=10):
        self.cam_index = cam_index
        self.cap = cv2.VideoCapture(self.cam_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera {cam_index}")

        self.face_cascade = cv2.CascadeClassifier(HAAR_PATH)

        # LBPH recognizer
        self.recognizer = None
        if os.path.exists(MODEL_PATH):
            try:
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
                self.recognizer.read(MODEL_PATH)
            except Exception as e:
                print("Failed to load LBPH model:", e)
                self.recognizer = None

        self.scale = scale_factor
        self.neighbors = min_neighbors
        self.label_map = self._build_label_map()

        # For alert cooldowns
        self.alert_cooldown = timedelta(seconds=alert_cooldown)
        self.last_alert_time = {}  # {name: datetime}

    # Build label map from dataset
    def _build_label_map(self):
        if not os.path.exists(DATASET_DIR):
            return {}
        entries = sorted([d for d in os.listdir(DATASET_DIR) if os.path.isdir(os.path.join(DATASET_DIR, d))])
        return {i: name for i, name in enumerate(entries)}

    def refresh_label_map(self):
        self.label_map = self._build_label_map()

    # Log recognition in SQLite
    def log_recognition(self, name, confidence):
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO logs (name, confidence, timestamp) VALUES (?, ?, ?)",
                      (name, float(confidence), datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()

    # Send alert to Flask web app (or any endpoint)
    def post_alert(self, name, confidence, notes=""):
        now = datetime.utcnow()
        # Check cooldown
        last_time = self.last_alert_time.get(name)
        if last_time and now - last_time < self.alert_cooldown:
            return
        self.last_alert_time[name] = now

        try:
            requests.post(
                "http://127.0.0.1:5000/api/alert",  # Flask SocketIO endpoint
                json={"name": name, "confidence": float(confidence), "notes": notes},
                timeout=1.5
            )
        except Exception as e:
            print("Alert post failed:", e)

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def generator(self):
        """Yield JPEG frames with detection/recognition drawn (for MJPEG streaming)."""
        while True:
            frame = self.get_frame()
            if frame is None:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, self.scale, self.neighbors)

            for (x, y, w, h) in faces:
                face_roi = gray[y:y+h, x:x+w]
                label_text = "Unknown"
                color = (0, 0, 255)  # red = unknown

                if self.recognizer is not None and len(self.label_map) > 0:
                    try:
                        id_, conf = self.recognizer.predict(face_roi)
                        if conf < 70 and id_ in self.label_map:
                            name = self.label_map[id_]
                            label_text = f"{name} ({conf:.1f})"
                            color = (0, 255, 0)
                            self.log_recognition(name, conf)
                            self.post_alert(name, conf, notes="recognized")
                        else:
                            name = "Unknown"
                            label_text = f"Unknown ({conf:.1f})"
                            color = (0, 0, 255)
                            self.post_alert(name, conf, notes="unknown face")
                    except Exception:
                        name = "Unknown"
                        label_text = "Unknown"
                        color = (0, 0, 255)
                        self.post_alert(name, 0, notes="prediction error")

                # Draw rectangle and label
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, label_text, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Encode as JPEG for streaming
            ret2, jpeg = cv2.imencode('.jpg', frame)
            if not ret2:
                continue
            frame_bytes = jpeg.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    def release(self):
        try:
            self.cap.release()
        except:
            pass
