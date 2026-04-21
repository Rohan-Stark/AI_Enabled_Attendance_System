"""
Teacher Routes — dashboard, attendance session, live video feed, export.
"""
import cv2
import logging
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, Response, jsonify, send_file, current_app
)
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import Student
from app.models.subject import Subject
from app.models.attendance import Attendance
from app.services.attendance_service import (
    generate_session_id, mark_attendance,
    get_subject_attendance_summary, get_session_students,
    get_low_attendance_students
)
from app.services.export_service import export_attendance_to_excel
from app.services.alert_service import send_bulk_alerts
from app.face_module.detector import FaceDetector
from app.face_module.recognizer import FaceRecognizer
from app.face_module.anti_spoof import AntiSpoof
from app.face_module.camera import Camera

from typing import Optional

logger = logging.getLogger(__name__)
teacher_bp = Blueprint("teacher", __name__)

# ── Module-level shared state for active session ───────────
_camera = None               # type: Optional[Camera]
_detector = None              # type: Optional[FaceDetector]
_recognizer = None            # type: Optional[FaceRecognizer]
_anti_spoof = None            # type: Optional[AntiSpoof]
_active_session = None        # type: Optional[dict]


def _require_teacher(f):
    """Decorator to ensure only teachers can access."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "teacher":
            flash("Access denied.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ────────────────────────────────────────────────────────────
#  DASHBOARD
# ────────────────────────────────────────────────────────────
@teacher_bp.route("/dashboard")
@login_required
@_require_teacher
def dashboard():
    """Teacher dashboard — lists subjects and attendance summaries."""
    subjects = Subject.query.filter_by(teacher_id=current_user.id).all()
    semester = request.args.get("semester", type=int)

    subject_data = []
    for subj in subjects:
        if semester and subj.semester != semester:
            continue
        summary = get_subject_attendance_summary(subj.id)
        subject_data.append({
            "subject": subj,
            "summary": summary
        })

    semesters = sorted(set(s.semester for s in subjects))
    return render_template(
        "teacher/dashboard.html",
        subject_data=subject_data,
        semesters=semesters,
        selected_semester=semester,
        active_session=_active_session
    )


# ────────────────────────────────────────────────────────────
#  ATTENDANCE SESSION
# ────────────────────────────────────────────────────────────
@teacher_bp.route("/start_session", methods=["POST"])
@login_required
@_require_teacher
def start_session():
    """Start a new attendance session for a subject."""
    global _camera, _detector, _recognizer, _anti_spoof, _active_session

    subject_id = request.form.get("subject_id", type=int)
    subject = Subject.query.get(subject_id)

    if not subject or subject.teacher_id != current_user.id:
        flash("Invalid subject.", "danger")
        return redirect(url_for("teacher.dashboard"))

    # Initialize face recognition pipeline
    config = current_app.config
    _detector = FaceDetector(
        model=config.get("FACE_RECOGNITION_MODEL", "hog"),
        num_jitters=config.get("FACE_ENCODING_JITTERS", 1)
    )
    _recognizer = FaceRecognizer(
        tolerance=config.get("FACE_RECOGNITION_TOLERANCE", 0.45)
    )
    _anti_spoof = AntiSpoof(
        ear_threshold=config.get("EAR_THRESHOLD", 0.21),
        consecutive_frames=config.get("EAR_CONSECUTIVE_FRAMES", 3),
        required_blinks=config.get("BLINK_REQUIRED_COUNT", 2)
    )

    # Load known faces for the subject's semester
    students = Student.query.filter_by(semester=subject.semester).all()
    _recognizer.load_known_faces(students)

    # Initialize camera
    _camera = Camera(
        resize_factor=config.get("FRAME_RESIZE_FACTOR", 0.25),
        process_every_n=config.get("PROCESS_EVERY_N_FRAMES", 2)
    )
    if not _camera.start():
        flash("Could not open webcam.", "danger")
        return redirect(url_for("teacher.dashboard"))

    # Create session
    session_id = generate_session_id(subject.code)
    _active_session = {
        "subject_id": subject.id,
        "subject_name": subject.name,
        "subject_code": subject.code,
        "session_id": session_id,
        "marked": set()
    }

    logger.info(f"Session started: {session_id}")
    flash(f"Session started: {session_id}", "success")
    return redirect(url_for("teacher.session_page"))


@teacher_bp.route("/session")
@login_required
@_require_teacher
def session_page():
    """Live attendance session page with webcam feed."""
    if not _active_session:
        flash("No active session.", "warning")
        return redirect(url_for("teacher.dashboard"))

    marked_students = get_session_students(_active_session["session_id"])
    return render_template(
        "teacher/session.html",
        session=_active_session,
        marked_students=marked_students
    )


@teacher_bp.route("/video_feed")
@login_required
@_require_teacher
def video_feed():
    """MJPEG video stream endpoint for the webcam."""
    if not _camera or not _camera.is_opened:
        return "Camera not available", 503

    return Response(
        _camera.generate_mjpeg(process_callback=_process_attendance_frame),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


def _process_attendance_frame(frame, small_frame):
    """
    Callback for each processable webcam frame.
    Detects faces, recognizes students, and marks attendance.
    """
    global _active_session

    if not _active_session or not _detector or not _recognizer:
        return frame

    # Detect faces on the small (resized) frame
    resize = current_app.config.get("FRAME_RESIZE_FACTOR", 0.25)
    locations = _detector.detect_faces(small_frame)
    encodings = _detector.encode_faces(small_frame, locations)

    # Scale locations back to original frame size
    scale = int(1 / resize)
    full_locations = [(t * scale, r * scale, b * scale, l * scale)
                      for (t, r, b, l) in locations]

    # Multiple face fraud detection
    if len(locations) > 1:
        logger.warning(f"Multiple faces ({len(locations)}) detected in frame")

    # Identify each face
    names = []
    for i, encoding in enumerate(encodings):
        student_id, name, dist = _recognizer.identify(encoding)

        if student_id and student_id not in _active_session["marked"]:
            # Crop face for image logging
            t, r, b, l = full_locations[i]
            face_crop = frame[max(0, t):b, max(0, l):r]

            result = mark_attendance(
                student_id=student_id,
                subject_id=_active_session["subject_id"],
                session_id=_active_session["session_id"],
                frame=face_crop,
                verified=True  # In live mode; anti-spoof can be added per-student
            )
            if result["success"]:
                _active_session["marked"].add(student_id)
                logger.info(f"Auto-marked: {name}")

            names.append(f"{name} ✓")
        elif student_id:
            names.append(f"{name} (done)")
        else:
            names.append("Unknown")

    # Draw bounding boxes on original frame
    annotated = _detector.draw_boxes(frame, full_locations, names)

    # Add session info overlay
    cv2.putText(annotated, f"Session: {_active_session['session_id']}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.putText(annotated, f"Marked: {len(_active_session['marked'])}",
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    return annotated


@teacher_bp.route("/stop_session", methods=["POST"])
@login_required
@_require_teacher
def stop_session():
    """Stop the active attendance session and release camera."""
    global _camera, _active_session

    if _camera:
        _camera.stop()
        _camera = None

    session_info = _active_session
    _active_session = None

    if session_info:
        flash(
            f"Session ended. {len(session_info['marked'])} students marked.",
            "success"
        )
    return redirect(url_for("teacher.dashboard"))


@teacher_bp.route("/session_data")
@login_required
@_require_teacher
def session_data():
    """Endpoint for AJAX polling of current session data."""
    if not _active_session:
        return jsonify({"active": False})

    students = get_session_students(_active_session["session_id"])
    return jsonify({
        "active": True,
        "session_id": _active_session["session_id"],
        "marked_count": len(_active_session["marked"]),
        "students": students
    })


# ────────────────────────────────────────────────────────────
#  EXPORT & ALERTS
# ────────────────────────────────────────────────────────────
@teacher_bp.route("/export/<int:subject_id>")
@login_required
@_require_teacher
def export(subject_id):
    """Export attendance report as Excel file."""
    subject = Subject.query.get(subject_id)
    if not subject or subject.teacher_id != current_user.id:
        flash("Invalid subject.", "danger")
        return redirect(url_for("teacher.dashboard"))

    filepath = export_attendance_to_excel(subject_id)
    if filepath:
        return send_file(filepath, as_attachment=True)

    flash("Export failed.", "danger")
    return redirect(url_for("teacher.dashboard"))


@teacher_bp.route("/send_alerts/<int:subject_id>", methods=["POST"])
@login_required
@_require_teacher
def send_alerts(subject_id):
    """Send low-attendance email alerts for a subject."""
    subject = Subject.query.get(subject_id)
    if not subject or subject.teacher_id != current_user.id:
        flash("Invalid subject.", "danger")
        return redirect(url_for("teacher.dashboard"))

    threshold = current_app.config.get("LOW_ATTENDANCE_THRESHOLD", 75)
    low = get_low_attendance_students(subject.semester, threshold)
    result = send_bulk_alerts(low, subject.name)

    flash(f"Alerts sent: {result['sent']}, Failed: {result['failed']}", "info")
    return redirect(url_for("teacher.dashboard"))
