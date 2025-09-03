import cv2
import os
import sqlite3
from database import init_db

# Ensure DB exists
init_db()

# Load face detector
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
cam = cv2.VideoCapture(0)

uid = input("Enter numeric ID for person (e.g. 101): ")
name = input("Enter name: ")

# Create dataset folder for this user
folder = f"dataset/{uid}"
os.makedirs(folder, exist_ok=True)

print('📸 Position your face. Press "s" to save the image or "q" to quit.')

saved = False
while True:
    ret, frame = cam.read()
    if not ret:
        print('❌ Failed to read from camera')
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        cv2.putText(frame, "Press 's' to save", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if cv2.waitKey(1) & 0xFF == ord('s') and not saved:
            # Save only one image per person
            img_path = f"{folder}/1.jpg"
            cv2.imwrite(img_path, gray[y:y+h, x:x+w])
            print(f'✅ Saved face image for ID {uid}: {img_path}')

            # Insert / update in database
            conn = sqlite3.connect("faceguard.db")
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO persons (id, name, image_path) VALUES (?, ?, ?)",
                      (uid, name, img_path))
            conn.commit()
            conn.close()

            saved = True

    cv2.imshow('Capture', frame)

    if cv2.waitKey(1) & 0xFF == ord('q') or saved:
        break

cam.release()
cv2.destroyAllWindows()
