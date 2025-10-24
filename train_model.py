import cv2
import os
import json
import numpy as np
from app import DATASET_DIR, MODEL_PATH, LABEL_MAP_PATH

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
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    recognizer.save(MODEL_PATH)

    # Save label map as JSON
    with open(LABEL_MAP_PATH, "w") as f:
        json.dump({str(k): v for k, v in label_map.items()}, f)

    print("Model saved to", MODEL_PATH)
    print("Label map saved to", LABEL_MAP_PATH)
    for k, v in label_map.items():
        print(k, "->", v)

if __name__ == "__main__":
    train()
