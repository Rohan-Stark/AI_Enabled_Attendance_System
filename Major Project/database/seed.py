"""
Database Seed Script — populates the database with demo data.
Run:  python -m database.seed
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.user import Admin, Teacher, Student
from app.models.subject import Subject


def seed():
    app = create_app()
    with app.app_context():
        print("🌱 Seeding database...")

        # ── Admin ──────────────────────────────────────────
        if not Admin.query.first():
            admin = Admin(name="System Admin", email="admin@university.edu")
            admin.set_password("admin123")
            db.session.add(admin)
            print("  ✓ Admin created: admin@university.edu / admin123")

        # ── Teachers ───────────────────────────────────────
        teachers_data = [
            {"name": "Dr. Sharma", "email": "sharma@university.edu", "password": "teacher123"},
            {"name": "Prof. Gupta", "email": "gupta@university.edu", "password": "teacher123"},
        ]
        for td in teachers_data:
            if not Teacher.query.filter_by(email=td["email"]).first():
                t = Teacher(name=td["name"], email=td["email"])
                t.set_password(td["password"])
                db.session.add(t)
                print(f"  ✓ Teacher created: {td['email']} / {td['password']}")

        db.session.commit()

        # ── Subjects ───────────────────────────────────────
        t1 = Teacher.query.filter_by(email="sharma@university.edu").first()
        t2 = Teacher.query.filter_by(email="gupta@university.edu").first()

        subjects_data = [
            {"name": "Data Structures", "code": "CS201", "semester": 3, "teacher_id": t1.id},
            {"name": "Operating Systems", "code": "CS301", "semester": 3, "teacher_id": t1.id},
            {"name": "Database Systems", "code": "CS302", "semester": 3, "teacher_id": t2.id},
            {"name": "Computer Networks", "code": "CS401", "semester": 4, "teacher_id": t2.id},
        ]
        for sd in subjects_data:
            if not Subject.query.filter_by(code=sd["code"]).first():
                s = Subject(**sd)
                db.session.add(s)
                print(f"  ✓ Subject created: {sd['code']} — {sd['name']}")

        # ── Students ───────────────────────────────────────
        students_data = [
            {"name": "Rohan Kumar", "email": "rohan@student.edu", "enrollment_no": "EN2024001", "semester": 3},
            {"name": "Priya Singh", "email": "priya@student.edu", "enrollment_no": "EN2024002", "semester": 3},
            {"name": "Amit Verma", "email": "amit@student.edu", "enrollment_no": "EN2024003", "semester": 3},
            {"name": "Sneha Patel", "email": "sneha@student.edu", "enrollment_no": "EN2024004", "semester": 4},
            {"name": "Rahul Joshi", "email": "rahul@student.edu", "enrollment_no": "EN2024005", "semester": 4},
        ]
        for sd in students_data:
            if not Student.query.filter_by(email=sd["email"]).first():
                s = Student(
                    name=sd["name"], email=sd["email"],
                    enrollment_no=sd["enrollment_no"], semester=sd["semester"]
                )
                s.set_password("student123")
                db.session.add(s)
                print(f"  ✓ Student created: {sd['email']} / student123")

        db.session.commit()
        print("\n✅ Database seeded successfully!")
        print("\n── Demo Credentials ──────────────────────")
        print("  Admin:   admin@university.edu / admin123")
        print("  Teacher: sharma@university.edu / teacher123")
        print("  Student: rohan@student.edu / student123")
        print("──────────────────────────────────────────")


if __name__ == "__main__":
    seed()
