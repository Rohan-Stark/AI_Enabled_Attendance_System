"""
Student Routes — attendance dashboard, history, subject-wise stats.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.subject import Subject
from app.services.attendance_service import get_student_attendance

student_bp = Blueprint("student", __name__)


def _require_student(f):
    """Decorator to ensure only students can access."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "student":
            flash("Access denied.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


@student_bp.route("/dashboard")
@login_required
@_require_student
def dashboard():
    """Student dashboard — attendance overview and subject-wise breakdown."""
    semester = request.args.get("semester", current_user.semester, type=int)

    # Get subjects for the selected semester
    subjects = Subject.query.filter_by(semester=semester).all()

    # Overall attendance
    overall = get_student_attendance(current_user.id)

    # Per-subject stats
    subject_stats = []
    for subj in subjects:
        stats = get_student_attendance(current_user.id, subj.id)
        subject_stats.append({
            "subject": subj,
            "stats": stats
        })

    semesters = list(range(1, 9))  # Semesters 1-8
    return render_template(
        "student/dashboard.html",
        overall=overall,
        subject_stats=subject_stats,
        semesters=semesters,
        selected_semester=semester
    )
