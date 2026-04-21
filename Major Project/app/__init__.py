"""
Application Factory — creates and configures the Flask app.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Ensure required directories exist ──────────────────
    for folder in [
        app.config.get("KNOWN_FACES_DIR", "data/known_faces"),
        app.config.get("CAPTURES_DIR", "app/static/captures"),
        app.config.get("EXPORT_DIR", "exports"),
        os.path.dirname(app.config.get("LOG_FILE", "logs/app.log")),
        os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance'),
    ]:
        os.makedirs(folder, exist_ok=True)

    # ── Initialize extensions ──────────────────────────────
    from app.extensions import db, login_manager, csrf
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    # ── Register blueprints ────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.teacher import teacher_bp
    from app.routes.student import student_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(teacher_bp, url_prefix="/teacher")
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # ── Create database tables ─────────────────────────────
    with app.app_context():
        from app.models import user, subject, attendance  # noqa: F401
        db.create_all()

    # ── Setup logging ──────────────────────────────────────
    _setup_logging(app)

    return app


def _setup_logging(app):
    """Configure rotating file logger."""
    log_file = app.config.get("LOG_FILE", "logs/app.log")
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"))

    handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5)
    handler.setLevel(log_level)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
    app.logger.info("Smart Attendance System started.")
