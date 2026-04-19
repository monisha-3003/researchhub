from app import app
from models import Scholar, Supervisor, User, SupervisorRequest

with app.app_context():
    print('--- SCHOLARS ---')
    for s in Scholar.query.all():
        print(f"ID: {s.id}, UserID: {s.user_id}, Name: {s.first_name} {s.last_name}, SupervisorID: {s.supervisor_id}")
    
    print('\n--- SUPERVISORS ---')
    for sv in Supervisor.query.all():
        print(f"ID: {sv.id}, UserID: {sv.user_id}, Name: {sv.first_name} {sv.last_name}")

    print('\n--- REQUESTS ---')
    for r in SupervisorRequest.query.all():
        print(f"ID: {r.id}, ScholarID: {r.scholar_id}, SupervisorID: {r.supervisor_id}, Status: {r.status}")
