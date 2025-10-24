import cv2
import os
import json
from datetime import datetime, timedelta
from app import LABEL_MAP_PATH, MODEL_PATH, HAAR_PATH, DATASET_DIR, app, db, RecognitionLog, socketio

class VideoCamera:
    def __init__(self, cam_index=0):
        self.cap = cv2.VideoCapture(cam_index)
        self.face_cascade = cv2.CascadeClassifier(HAAR_PATH)
        self.recognizer = None
        self.label_map = {}
        if os.path.exists(MODEL_PATH):
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.recognizer.read(MODEL_PATH)
        if os.path.exists(LABEL_MAP_PATH):
            with open(LABEL_MAP_PATH, "r") as f:
                self.label_map = json.load(f)
        self.alert_cooldown = timedelta(seconds=10)
        self.last_alert_time = {}

    def refresh_label_map(self):
        if os.path.exists(LABEL_MAP_PATH):
            with open(LABEL_MAP_PATH, "r") as f:
                self.label_map = json.load(f)

    def get_frame(self):
        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        self.cap.release()
