# capture_faces.py
import cv2
import os

HAAR_PATH = "haarcascade_frontalface_default.xml"
DATASET_DIR = "dataset"
cam_index = 0
num_samples = 40

def capture_for_person(name):
    os.makedirs(DATASET_DIR, exist_ok=True)
    person_dir = os.path.join(DATASET_DIR, name)
    os.makedirs(person_dir, exist_ok=True)

    cap = cv2.VideoCapture(cam_index)
    face_cascade = cv2.CascadeClassifier(HAAR_PATH)
    count = 0
    print("Press 'q' to quit early. Capturing will stop after", num_samples, "samples.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            count += 1
            path = os.path.join(person_dir, f"{name}_{count:03d}.jpg")
            cv2.imwrite(path, face)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(frame, f"Captured: {count}/{num_samples}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.imshow("Capture Faces - Press q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if count >= num_samples:
            break
    cap.release()
    cv2.destroyAllWindows()
    print("Done. Saved", count, "images to", person_dir)

if __name__ == "__main__":
    name = input("Enter person name (no spaces): ").strip()
    if name:
        capture_for_person(name)
    else:
        print("Invalid name.")
