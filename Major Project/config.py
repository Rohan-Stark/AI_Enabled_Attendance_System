"""
Central Configuration for Smart Attendance System.
All tunable parameters live here — face recognition tolerance,
anti-spoofing thresholds, SMTP settings, paths, etc.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ── Flask ──────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key-change-in-prod")
    DEBUG = True

    # ── Database ───────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'attendance.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Face Recognition ───────────────────────────────────
    FACE_RECOGNITION_TOLERANCE = 0.45          # Lower = stricter matching
    FACE_RECOGNITION_MODEL = "hog"             # "hog" (CPU) or "cnn" (GPU)
    FRAME_RESIZE_FACTOR = 0.25                 # Resize webcam frames for speed
    PROCESS_EVERY_N_FRAMES = 2                 # Skip frames for performance
    FACE_ENCODING_JITTERS = 1                  # More jitters = more accurate but slower

    # ── Anti-Spoofing (Blink Detection) ────────────────────
    EAR_THRESHOLD = 0.21                       # Eye Aspect Ratio below this = blink
    EAR_CONSECUTIVE_FRAMES = 3                 # Consecutive low-EAR frames to count as blink
    BLINK_REQUIRED_COUNT = 2                   # Blinks needed to verify liveness

    # ── Attendance ─────────────────────────────────────────
    LOW_ATTENDANCE_THRESHOLD = 75              # Percentage — below triggers alert
    DUPLICATE_WINDOW_MINUTES = 60              # Prevent re-marking within this window

    # ── SMTP Email Alerts ──────────────────────────────────
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    ALERT_FROM_EMAIL = os.environ.get("ALERT_FROM_EMAIL", "attendance@university.edu")

    # ── File Paths ─────────────────────────────────────────
    KNOWN_FACES_DIR = os.path.join(BASE_DIR, "data", "known_faces")
    CAPTURES_DIR = os.path.join(BASE_DIR, "app", "static", "captures")
    EXPORT_DIR = os.path.join(BASE_DIR, "exports")

    # ── Logging ────────────────────────────────────────────
    LOG_FILE = os.path.join(BASE_DIR, "logs", "app.log")
    LOG_LEVEL = "INFO"
