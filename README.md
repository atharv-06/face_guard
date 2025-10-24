# Real-Time Face Recognition Web App

A Flask-based real-time face recognition system with:

- Live video streaming via webcam
- Face detection & recognition (LBPH)
- Unknown face alerts via a top notification bar
- SQLite logging of unknown faces
- Admin dashboard for users & blacklist
- Dataset management and model training

---

## Project Structure

```
.
├── app.py
├── camera.py
├── capture_faces.py
├── train_model.py
├── models.py
├── auth.py
├── templates/
├── dataset/
├── trained_model/
├── database/
└── requirements.txt
```

---

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Add Faces

```bash
python capture_faces.py
```

- Enter person name (no spaces)
- Captures ~40 images per person

---

## Train Model

```bash
python train_model.py
```

- Generates:
  - `trained_model/lbph.yml` → LBPH model
  - `trained_model/label_map.json` → ID-to-name map

---

## Run the App

```bash
python app.py
```

- Access: [http://localhost:5000](http://localhost:5000)
- Default admin credentials:
  - Username: `admin`
  - Password: `admin123` (change after first login)

---

## Usage

- **Live Feed:** Unknown faces trigger a red notification bar at the top
- **Dashboard:** View logs, statistics
- **Users:** Create/delete users and assign roles
- **Blacklist:** Add names to block and trigger alerts
- **Dataset:** Refresh label map after training new faces

---

## Dependencies

- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-SocketIO
- eventlet
- OpenCV
- NumPy

---

## Notes

- Only unknown faces trigger alerts/logging
- Ensure your webcam is free and connected
- Run `train_model.py` after adding new faces
