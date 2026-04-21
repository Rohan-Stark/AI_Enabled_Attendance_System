"""
Auth Routes — login, logout, role-based redirect.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import Admin, Teacher, Student

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    """Redirect to login or appropriate dashboard."""
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page with role selection.
    GET: render login form.
    POST: authenticate and redirect.
    """
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == "POST":
        role = request.form.get("role", "").lower()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        model_map = {"admin": Admin, "teacher": Teacher, "student": Student}
        model = model_map.get(role)

        if not model:
            flash("Invalid role selected.", "danger")
            return redirect(url_for("auth.login"))

        user = model.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f"Welcome, {user.name}!", "success")
            return _redirect_by_role(user)
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))


def _redirect_by_role(user):
    """Redirect user to their role-specific dashboard."""
    role = getattr(user, "role", "")
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    elif role == "teacher":
        return redirect(url_for("teacher.dashboard"))
    elif role == "student":
        return redirect(url_for("student.dashboard"))
    return redirect(url_for("auth.login"))
