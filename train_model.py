# train_model.py
import cv2
import os
import numpy as np

DATASET_DIR = "dataset"
MODEL_DIR = "trained_model"
MODEL_PATH = os.path.join(MODEL_DIR, "lbph.yml")

def train():
    faces = []
    ids = []
    label_map = {}
    cur_id = 0
    for person in sorted(os.listdir(DATASET_DIR)):
        person_dir = os.path.join(DATASET_DIR, person)
        if not os.path.isdir(person_dir):
            continue
        label_map[cur_id] = person
        for fname in os.listdir(person_dir):
            path = os.path.join(person_dir, fname)
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            faces.append(img)
            ids.append(cur_id)
        cur_id += 1

    if len(faces) == 0:
        print("No faces found in dataset. Capture faces first.")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(ids))

    os.makedirs(MODEL_DIR, exist_ok=True)
    recognizer.save(MODEL_PATH)
    print("Model saved to", MODEL_PATH)
    # print label map for reference
    for k, v in label_map.items():
        print(k, "->", v)

if __name__ == "__main__":
    train()
