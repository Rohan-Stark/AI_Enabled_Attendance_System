"""
Alert Service — sends email notifications for low attendance via SMTP.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

logger = logging.getLogger(__name__)


def send_low_attendance_alert(student_name: str, student_email: str,
                              percentage: float, subject_name: str) -> bool:
    """
    Send an email alert to a student about low attendance.

    Returns:
        True if sent successfully, False otherwise.
    """
    smtp_server = current_app.config.get("SMTP_SERVER", "")
    smtp_port = current_app.config.get("SMTP_PORT", 587)
    smtp_user = current_app.config.get("SMTP_USERNAME", "")
    smtp_pass = current_app.config.get("SMTP_PASSWORD", "")
    from_email = current_app.config.get("ALERT_FROM_EMAIL", "")

    if not all([smtp_server, smtp_user, smtp_pass]):
        logger.warning("SMTP not configured — skipping email alert")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"⚠️ Low Attendance Alert — {subject_name}"
        msg["From"] = from_email
        msg["To"] = student_email

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #e74c3c;">Low Attendance Warning</h2>
            <p>Dear <strong>{student_name}</strong>,</p>
            <p>Your attendance in <strong>{subject_name}</strong> has fallen to
               <strong style="color: #e74c3c;">{percentage}%</strong>,
               which is below the minimum requirement of
               <strong>{current_app.config.get('LOW_ATTENDANCE_THRESHOLD', 75)}%</strong>.</p>
            <p>Please ensure regular attendance to avoid any academic penalties.</p>
            <hr>
            <p style="font-size: 0.85em; color: #888;">
                — Smart Attendance System
            </p>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, student_email, msg.as_string())

        logger.info(f"Alert sent to {student_email} (attendance: {percentage}%)")
        return True

    except Exception as e:
        logger.error(f"Failed to send alert to {student_email}: {e}")
        return False


def send_bulk_alerts(low_students: list, subject_name: str) -> dict:
    """
    Send alerts to all students with low attendance.

    Args:
        low_students: List of dicts with 'name', 'email', 'percentage'.
        subject_name: Name of the subject.

    Returns:
        {'sent': int, 'failed': int}
    """
    sent = 0
    failed = 0
    for s in low_students:
        success = send_low_attendance_alert(
            s["name"], s["email"], s["percentage"], subject_name
        )
        if success:
            sent += 1
        else:
            failed += 1

    logger.info(f"Bulk alerts: {sent} sent, {failed} failed")
    return {"sent": sent, "failed": failed}
