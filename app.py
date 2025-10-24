# app.py
import os
import json
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_socketio import SocketIO
import cv2

# ----------------- Config -----------------
basedir = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(basedir, "database", "app.db")
MODEL_PATH = os.path.join(basedir, "trained_model", "lbph.yml")
LABEL_MAP_PATH = os.path.join(basedir, "trained_model", "label_map.json")
DATASET_DIR = os.path.join(basedir, "dataset")
HAAR_PATH = os.path.join(basedir, "haarcascade_frontalface_default.xml")

os.makedirs(os.path.join(basedir, "database"), exist_ok=True)
os.makedirs(os.path.join(basedir, "trained_model"), exist_ok=True)

# ----------------- Flask & Extensions -----------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

# ----------------- Models -----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pwd):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(pwd)

    def check_password(self, pwd):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, pwd)

    def is_admin(self):
        return self.role == "admin"

class RecognitionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    confidence = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Blacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)

# ----------------- Create Tables -----------------
with app.app_context():
    db.create_all()

# ----------------- Login -----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class UserLogin(UserMixin):
    def __init__(self, user):
        self._user = user

    @property
    def id(self):
        return str(self._user.id)
    
    @property
    def username(self):
        return self._user.username

@login_manager.user_loader
def load_user(user_id):
    u = User.query.get(int(user_id))
    if u:
        return UserLogin(u)
    return None

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        u = User.query.get(int(current_user.id))
        if not u or u.role != "admin":
            flash("Admin access required", "warning")
            return redirect(url_for("dashboard"))
        return func(*args, **kwargs)
    return wrapper

# ----------------- Camera -----------------
class VideoCamera:
    def __init__(self, cam_index=0):
        self.cap = cv2.VideoCapture(cam_index)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")
        self.face_cascade = cv2.CascadeClassifier(HAAR_PATH)
        self.recognizer = None
        self.label_map = {}
        if os.path.exists(MODEL_PATH):
            try:
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
                self.recognizer.read(MODEL_PATH)
                if os.path.exists(LABEL_MAP_PATH):
                    with open(LABEL_MAP_PATH, "r") as f:
                        self.label_map = json.load(f)
            except Exception as e:
                print("Error loading model:", e)

        self.alert_cooldown = timedelta(seconds=10)
        self.last_alert_time = {}

    def refresh_label_map(self):
        if os.path.exists(LABEL_MAP_PATH):
            with open(LABEL_MAP_PATH, "r") as f:
                self.label_map = json.load(f)

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def generator(self):
        while True:
            frame = self.get_frame()
            if frame is None:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                face_roi = gray[y:y+h, x:x+w]
                label_text = "Unknown"
                color = (0, 0, 255)
                if self.recognizer and self.label_map:
                    try:
                        id_, conf = self.recognizer.predict(face_roi)
                        name = self.label_map.get(str(id_), "Unknown")
                        if conf < 70:
                            label_text = f"{name} ({conf:.1f})"
                            color = (0, 255, 0)
                        else:
                            name = "Unknown"
                            label_text = f"Unknown ({conf:.1f})"
                        # log & alert inside app context
                        now = datetime.utcnow()
                        with app.app_context():
                            if self.last_alert_time.get(name) is None or now - self.last_alert_time[name] > self.alert_cooldown:
                                self.last_alert_time[name] = now
                                log = RecognitionLog(name=name, confidence=conf)
                                db.session.add(log)
                                db.session.commit()
                                socketio.emit("face_detected", {"name": name, "confidence": conf})
                    except Exception:
                        pass
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, label_text, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            ret2, jpeg = cv2.imencode('.jpg', frame)
            if not ret2:
                continue
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

    def release(self):
        self.cap.release()

camera = VideoCamera()

# ----------------- Routes -----------------
@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/video_feed")
@login_required
def video_feed():
    return Response(camera.generator(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# -------- Login & Logout --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(UserLogin(user))
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("rb_login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out", "info")
    return redirect(url_for("login"))

# -------- Dashboard --------
@app.route("/dashboard")
@login_required
def dashboard():
    total = RecognitionLog.query.count()
    recent = RecognitionLog.query.order_by(RecognitionLog.timestamp.desc()).limit(10).all()
    bl_count = Blacklist.query.filter_by(active=True).count()
    return render_template("rb_dashboard.html", total=total, recent=recent, bl_count=bl_count)

# ----------------- Initialize default admin -----------------
with app.app_context():
    if User.query.filter_by(username="admin").first() is None:
        admin = User(username="admin", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Default admin created: admin/admin123")

# ----------------- Run -----------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
