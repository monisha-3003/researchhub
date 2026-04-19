import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app import app
from models import Supervisor, Scholar, User

with app.app_context():
    print("=== SUPERVISORS ===")
    svs = Supervisor.query.all()
    for sv in svs:
        u = User.query.get(sv.user_id)
        scholars = Scholar.query.filter_by(supervisor_id=sv.id).all()
        email = u.email if u else "NO USER"
        print(f"  ID={sv.id} user_id={sv.user_id} name={sv.first_name} {sv.last_name} email={email} scholars={len(scholars)}")

    print()
    print("=== SCHOLARS ===")
    scholars = Scholar.query.all()
    for s in scholars:
        print(f"  ID={s.id} name={s.first_name} {s.last_name} supervisor_id={s.supervisor_id}")

    print()
    print("=== USERS (faculty/supervisor role) ===")
    users = User.query.filter(User.role.in_(['faculty','supervisor'])).all()
    for u in users:
        print(f"  user_id={u.id} email={u.email} role={u.role}")
