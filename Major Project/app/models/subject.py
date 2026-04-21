"""
Subject model — represents a course/subject taught by a teacher in a semester.
"""
from app.extensions import db


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    semester = db.Column(db.Integer, nullable=False)

    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)

    attendance_records = db.relationship("Attendance", backref="subject", lazy=True)

    def __repr__(self):
        return f"<Subject {self.code} — {self.name}>"
