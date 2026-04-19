import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app import app
from models import Scholar, User

with app.app_context():
    print("=== ALL SCHOLARS WITH LOGIN DETAILS ===")
    scholars = Scholar.query.all()
    for s in scholars:
        u = User.query.get(s.user_id)
        email = u.email if u else "NO USER"
        role  = u.role  if u else "N/A"
        print(f"  Name: {s.first_name} {s.last_name} | Enrollment: {s.enrollment_id} | Email: {email} | Role: {role} | Password: password123")
