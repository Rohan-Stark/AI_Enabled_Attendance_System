"""
Attendance model — one record per student per attendance session.
Tracks verification status, captured face image, and timestamps.
"""
from datetime import datetime, timezone
from app.extensions import db


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)

    # Unique session identifier (e.g. "SUBJ101-2026-04-09-10:00")
    session_id = db.Column(db.String(100), nullable=False)

    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default="present")       # present / absent / late
    capture_path = db.Column(db.String(300), nullable=True)     # Path to face capture image
    verified = db.Column(db.Boolean, default=False)             # Anti-spoof verified

    # Prevent duplicate marking in the same session
    __table_args__ = (
        db.UniqueConstraint("student_id", "session_id", name="uq_student_session"),
    )

    def __repr__(self):
        return f"<Attendance student={self.student_id} session={self.session_id}>"
