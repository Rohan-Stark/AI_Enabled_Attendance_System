"""
Attendance Service — business logic for marking and querying attendance.
Handles duplicate prevention, analytics, and fraud detection.
"""
import os
import cv2
import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from flask import current_app
from sqlalchemy import func
from app.extensions import db
from app.models.attendance import Attendance
from app.models.user import Student
from app.models.subject import Subject

logger = logging.getLogger(__name__)


def generate_session_id(subject_code: str) -> str:
    """Generate a unique session identifier."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")
    return f"{subject_code}-{now}"


def mark_attendance(student_id: int, subject_id: int, session_id: str,
                    frame=None, verified: bool = False) -> dict:
    """
    Mark a student as present for a given session.

    Fraud Prevention:
      - Checks for duplicate marking in same session.
      - Checks for re-marking within DUPLICATE_WINDOW_MINUTES.

    Image Logging:
      - Saves the captured face frame to disk with timestamp.

    Returns:
        {'success': bool, 'message': str, 'attendance_id': int|None}
    """
    # ── Duplicate check ────────────────────────────────────
    existing = Attendance.query.filter_by(
        student_id=student_id, session_id=session_id
    ).first()
    if existing:
        return {
            "success": False,
            "message": "Attendance already marked for this session",
            "attendance_id": existing.id
        }

    # ── Time-window duplicate check ────────────────────────
    window = current_app.config.get("DUPLICATE_WINDOW_MINUTES", 60)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window)
    recent = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.subject_id == subject_id,
        Attendance.timestamp >= cutoff
    ).first()
    if recent:
        return {
            "success": False,
            "message": f"Already marked within the last {window} minutes",
            "attendance_id": recent.id
        }

    # ── Save captured face image ───────────────────────────
    capture_path = None
    if frame is not None:
        captures_dir = current_app.config.get("CAPTURES_DIR", "app/static/captures")
        os.makedirs(captures_dir, exist_ok=True)
        filename = f"{student_id}_{session_id}_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join(captures_dir, filename)
        cv2.imwrite(filepath, frame)
        capture_path = f"captures/{filename}"
        logger.info(f"Face capture saved: {filepath}")

    # ── Create attendance record ───────────────────────────
    record = Attendance(
        student_id=student_id,
        subject_id=subject_id,
        session_id=session_id,
        status="present",
        capture_path=capture_path,
        verified=verified
    )
    db.session.add(record)
    db.session.commit()

    logger.info(f"Attendance marked: student={student_id}, session={session_id}")
    return {
        "success": True,
        "message": "Attendance marked successfully",
        "attendance_id": record.id
    }


def get_student_attendance(student_id: int, subject_id: int = None) -> dict:
    """
    Get attendance statistics for a student.

    Returns:
        {
            'total_sessions': int,
            'present_count': int,
            'percentage': float,
            'records': list[dict]
        }
    """
    query = Attendance.query.filter_by(student_id=student_id)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)

    records = query.order_by(Attendance.timestamp.desc()).all()

    # Count unique sessions for the subjects this student is enrolled in
    semester = Student.query.get(student_id).semester
    subject_filter = Subject.query.filter_by(semester=semester)
    if subject_id:
        subject_filter = subject_filter.filter_by(id=subject_id)

    subject_ids = [s.id for s in subject_filter.all()]

    total_sessions = db.session.query(
        func.count(func.distinct(Attendance.session_id))
    ).filter(Attendance.subject_id.in_(subject_ids)).scalar() or 0

    present_count = len(records)
    percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0.0

    return {
        "total_sessions": total_sessions,
        "present_count": present_count,
        "percentage": round(percentage, 1),
        "records": [
            {
                "id": r.id,
                "subject_id": r.subject_id,
                "session_id": r.session_id,
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M"),
                "status": r.status,
                "verified": r.verified
            }
            for r in records
        ]
    }


def get_subject_attendance_summary(subject_id: int) -> List[dict]:
    """
    Get attendance summary for all students in a subject.
    Used for teacher dashboard.

    Returns:
        List of {student_id, name, enrollment_no, present, total, percentage}
    """
    subject = Subject.query.get(subject_id)
    if not subject:
        return []

    students = Student.query.filter_by(semester=subject.semester).all()

    # Total unique sessions for this subject
    total_sessions = db.session.query(
        func.count(func.distinct(Attendance.session_id))
    ).filter_by(subject_id=subject_id).scalar() or 0

    results = []
    for s in students:
        present = Attendance.query.filter_by(
            student_id=s.id, subject_id=subject_id
        ).count()
        pct = (present / total_sessions * 100) if total_sessions > 0 else 0.0
        results.append({
            "student_id": s.id,
            "name": s.name,
            "enrollment_no": s.enrollment_no,
            "present": present,
            "total": total_sessions,
            "percentage": round(pct, 1)
        })

    return results


def get_low_attendance_students(semester: int, threshold: float = 75.0) -> List[dict]:
    """
    Find students with attendance below threshold.
    Used for alert system.
    """
    subjects = Subject.query.filter_by(semester=semester).all()
    low = []
    students = Student.query.filter_by(semester=semester).all()

    for student in students:
        stats = get_student_attendance(student.id)
        if stats["percentage"] < threshold:
            low.append({
                "student_id": student.id,
                "name": student.name,
                "email": student.email,
                "enrollment_no": student.enrollment_no,
                "percentage": stats["percentage"]
            })

    return low


def get_session_students(session_id: str) -> List[dict]:
    """Get list of students marked present in a specific session."""
    records = Attendance.query.filter_by(session_id=session_id).all()
    return [
        {
            "student_id": r.student_id,
            "name": r.student.name,
            "enrollment_no": r.student.enrollment_no,
            "timestamp": r.timestamp.strftime("%H:%M:%S"),
            "verified": r.verified,
            "capture_path": r.capture_path
        }
        for r in records
    ]
