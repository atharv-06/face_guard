import cv2
import sqlite3, time
from datetime import datetime
import os

# Load Haar Cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Load recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer.yml")

cap = cv2.VideoCapture(0)
os.makedirs("static/logs", exist_ok=True)

# ✅ Keep track of last seen person
last_seen = {}

def already_logged(person_id, status, cooldown=30):
    """
    Prevent duplicate logs.
    cooldown = seconds before same person can be logged again.
    """
    now = time.time()
    if person_id in last_seen:
        if now - last_seen[person_id] < cooldown:
            return True
    last_seen[person_id] = now
    return False

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Camera not available")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        try:
            id_, conf = recognizer.predict(roi_gray)
        except:
            id_, conf = None, 1000

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect("faceguard.db")
        c = conn.cursor()

        if conf < 50 and id_ is not None:   # ✅ Recognized
            student_id = str(id_)
            status = "Present"

            if not already_logged(student_id, status):
                img_name = f"static/logs/{student_id}_{int(time.time())}.jpg"
                cv2.imwrite(img_name, frame[y:y+h, x:x+w])

                c.execute("INSERT INTO logs(person_id, timestamp, status, snapshot) VALUES (?, ?, ?, ?)",
                          (student_id, timestamp, status, img_name))
                conn.commit()

                cv2.putText(frame, f"{student_id} - Attendance marked ✅",
                            (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

        else:   # 🚨 Intruder
            status = "Intruder"

            if not already_logged("intruder", status):
                img_name = f"static/logs/intruder_{int(time.time())}.jpg"
                cv2.imwrite(img_name, frame[y:y+h, x:x+w])

                c.execute("INSERT INTO logs(person_id, timestamp, status, snapshot) VALUES (?, ?, ?, ?)",
                          (None, timestamp, status, img_name))
                conn.commit()

                cv2.putText(frame, "🚨 Intruder detected!", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

        conn.close()

    cv2.imshow("Face Guard", frame)

    if cv2.waitKey(1) == 27:  # ESC to quit
        break

cap.release()
cv2.destroyAllWindows()
