"""
Admin Routes — manage users, register student faces, system overview.
"""
import os
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, current_app
)
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import Admin, Teacher, Student
from app.models.subject import Subject
from app.models.attendance import Attendance
from app.face_module.detector import FaceDetector
from werkzeug.utils import secure_filename

admin_bp = Blueprint("admin", __name__)


def _require_admin(f):
    """Decorator to ensure only admins can access."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Access denied.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ────────────────────────────────────────────────────────────
#  DASHBOARD
# ────────────────────────────────────────────────────────────
@admin_bp.route("/dashboard")
@login_required
@_require_admin
def dashboard():
    """Admin dashboard — system overview."""
    stats = {
        "students": Student.query.count(),
        "teachers": Teacher.query.count(),
        "subjects": Subject.query.count(),
        "attendance_records": Attendance.query.count(),
    }
    students = Student.query.order_by(Student.name).all()
    teachers = Teacher.query.order_by(Teacher.name).all()
    subjects = Subject.query.order_by(Subject.semester, Subject.name).all()

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        students=students,
        teachers=teachers,
        subjects=subjects
    )


# ────────────────────────────────────────────────────────────
#  ADD TEACHER
# ────────────────────────────────────────────────────────────
@admin_bp.route("/add_teacher", methods=["POST"])
@login_required
@_require_admin
def add_teacher():
    """Add a new teacher."""
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not all([name, email, password]):
        flash("All fields are required.", "danger")
        return redirect(url_for("admin.dashboard"))

    if Teacher.query.filter_by(email=email).first():
        flash("Teacher with this email already exists.", "danger")
        return redirect(url_for("admin.dashboard"))

    teacher = Teacher(name=name, email=email)
    teacher.set_password(password)
    db.session.add(teacher)
    db.session.commit()

    flash(f"Teacher '{name}' added.", "success")
    return redirect(url_for("admin.dashboard"))


# ────────────────────────────────────────────────────────────
#  ADD STUDENT + FACE REGISTRATION
# ────────────────────────────────────────────────────────────
@admin_bp.route("/add_student", methods=["POST"])
@login_required
@_require_admin
def add_student():
    """Add a new student and optionally register their face."""
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    enrollment_no = request.form.get("enrollment_no", "").strip()
    password = request.form.get("password", "")
    semester = request.form.get("semester", 1, type=int)
    face_image = request.files.get("face_image")

    if not all([name, email, enrollment_no, password]):
        flash("All fields are required.", "danger")
        return redirect(url_for("admin.dashboard"))

    if Student.query.filter_by(email=email).first():
        flash("Student with this email already exists.", "danger")
        return redirect(url_for("admin.dashboard"))

    if Student.query.filter_by(enrollment_no=enrollment_no).first():
        flash("Enrollment number already exists.", "danger")
        return redirect(url_for("admin.dashboard"))

    student = Student(name=name, email=email, enrollment_no=enrollment_no, semester=semester)
    student.set_password(password)

    # ── Face registration ──────────────────────────────────
    if face_image and face_image.filename:
        known_dir = current_app.config.get("KNOWN_FACES_DIR", "data/known_faces")
        os.makedirs(known_dir, exist_ok=True)
        filename = secure_filename(f"{enrollment_no}_{face_image.filename}")
        filepath = os.path.join(known_dir, filename)
        face_image.save(filepath)

        detector = FaceDetector(
            model=current_app.config.get("FACE_RECOGNITION_MODEL", "hog")
        )
        encoding = detector.encode_single_image(filepath)
        if encoding is not None:
            student.set_face_encoding(encoding)
            student.face_image_path = filepath
            flash(f"Face registered for {name}.", "success")
        else:
            flash(f"No face detected in uploaded image for {name}.", "warning")

    db.session.add(student)
    db.session.commit()

    flash(f"Student '{name}' added.", "success")
    return redirect(url_for("admin.dashboard"))


# ────────────────────────────────────────────────────────────
#  ADD SUBJECT
# ────────────────────────────────────────────────────────────
@admin_bp.route("/add_subject", methods=["POST"])
@login_required
@_require_admin
def add_subject():
    """Add a new subject."""
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip()
    semester = request.form.get("semester", 1, type=int)
    teacher_id = request.form.get("teacher_id", type=int)

    if not all([name, code, teacher_id]):
        flash("All fields are required.", "danger")
        return redirect(url_for("admin.dashboard"))

    if Subject.query.filter_by(code=code).first():
        flash("Subject code already exists.", "danger")
        return redirect(url_for("admin.dashboard"))

    subject = Subject(name=name, code=code, semester=semester, teacher_id=teacher_id)
    db.session.add(subject)
    db.session.commit()

    flash(f"Subject '{name}' added.", "success")
    return redirect(url_for("admin.dashboard"))


# ────────────────────────────────────────────────────────────
#  DELETE OPERATIONS
# ────────────────────────────────────────────────────────────
@admin_bp.route("/delete_student/<int:student_id>", methods=["POST"])
@login_required
@_require_admin
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    Attendance.query.filter_by(student_id=student.id).delete()
    db.session.delete(student)
    db.session.commit()
    flash(f"Student '{student.name}' deleted.", "info")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/delete_teacher/<int:teacher_id>", methods=["POST"])
@login_required
@_require_admin
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    db.session.delete(teacher)
    db.session.commit()
    flash(f"Teacher '{teacher.name}' deleted.", "info")
    return redirect(url_for("admin.dashboard"))
