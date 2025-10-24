# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user")  # 'admin' or 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pwd):
        self.password_hash = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password_hash, pwd)

    def is_admin(self):
        return self.role == "admin"

# recognition logs - can be integrated with existing logs table or used separately
class RecognitionLog(db.Model):
    __tablename__ = "recognition_logs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    confidence = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    camera = db.Column(db.String(100), nullable=True)

class Blacklist(db.Model):
    __tablename__ = "blacklist"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
