"""
User models — Student, Teacher, Admin.
Each role is a separate table for clarity and extensibility.
Password hashing via Werkzeug; face encoding stored as pickled blob for students.
"""
import pickle
from typing import Optional
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db, login_manager


# ── Admin ──────────────────────────────────────────────────
class Admin(UserMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="admin")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"admin-{self.id}"


# ── Teacher ────────────────────────────────────────────────
class Teacher(UserMixin, db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="teacher")

    subjects = db.relationship("Subject", backref="teacher", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"teacher-{self.id}"


# ── Student ────────────────────────────────────────────────
class Student(UserMixin, db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    enrollment_no = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    semester = db.Column(db.Integer, nullable=False, default=1)
    role = db.Column(db.String(20), default="student")

    # Face encoding stored as pickled numpy array (128-d vector)
    face_encoding_blob = db.Column(db.LargeBinary, nullable=True)
    face_image_path = db.Column(db.String(300), nullable=True)

    attendance_records = db.relationship("Attendance", backref="student", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"student-{self.id}"

    # ── Face encoding helpers ──────────────────────────────
    def set_face_encoding(self, encoding: np.ndarray):
        """Serialize a 128-d numpy array to binary for DB storage."""
        self.face_encoding_blob = pickle.dumps(encoding)

    def get_face_encoding(self) -> Optional[np.ndarray]:
        """Deserialize stored face encoding."""
        if self.face_encoding_blob:
            return pickle.loads(self.face_encoding_blob)
        return None


# ── Flask-Login user loader ────────────────────────────────
@login_manager.user_loader
def load_user(user_id: str):
    """
    user_id is stored as 'role-id', e.g. 'student-5'.
    This lets Flask-Login disambiguate across tables.
    """
    try:
        role, uid = user_id.split("-", 1)
        uid = int(uid)
    except (ValueError, AttributeError):
        return None

    model_map = {"admin": Admin, "teacher": Teacher, "student": Student}
    model = model_map.get(role)
    if model:
        return db.session.get(model, uid)
    return None
