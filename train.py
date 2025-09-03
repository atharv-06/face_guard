import cv2
import os
import numpy as np
from PIL import Image

# Initialize recognizer and Haar Cascade
recognizer = cv2.face.LBPHFaceRecognizer_create()
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

dataset_path = 'dataset'
faces = []
ids = []

# Loop through dataset folders
for user in os.listdir(dataset_path):
    if not user.isdigit():
        continue  # skip non-numeric folders
    uid = int(user)
    user_folder = os.path.join(dataset_path, user)

    for img_name in os.listdir(user_folder):
        img_path = os.path.join(user_folder, img_name)
        pil_img = Image.open(img_path).convert('L')  # convert to grayscale
        img_np = np.array(pil_img, 'uint8')

        # Detect faces
        detected = face_cascade.detectMultiScale(img_np)
        for (x, y, w, h) in detected:
            faces.append(img_np[y:y+h, x:x+w])
            ids.append(uid)

# Check if any faces were collected
if len(faces) == 0:
    print('No faces found. Capture images first.')
    exit()

# Train recognizer
recognizer.train(faces, np.array(ids))

# Save trained model
os.makedirs('trainer', exist_ok=True)
recognizer.write('trainer/trainer.yml')
print('✅ Training complete. Model saved to trainer/trainer.yml')
