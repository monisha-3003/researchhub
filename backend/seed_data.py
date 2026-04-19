import sys, os, random
from datetime import datetime, timedelta
from app import app
from models import Scholar, Attendance, LeaveRequest, Milestone, Publication, db

with app.app_context():
    scholars = Scholar.query.all()
    
    # 1. Add some Milestones
    for s in scholars:
        # Clear existing
        Milestone.query.filter_by(scholar_id=s.id).delete()
        
        milestones = [
            ("Literature Review", "completed"),
            ("Research Proposal", "completed"),
            ("Data Collection", "in_progress"),
            ("Methodology Draft", "pending")
        ]
        for title, status in milestones:
            m = Milestone(
                scholar_id=s.id,
                title=title,
                status=status,
                due_date=(datetime.now() + timedelta(days=random.randint(30, 180))).date()
            )
            db.session.add(m)

    # 2. Add some Attendance
    for s in scholars:
        Attendance.query.filter_by(scholar_id=s.id).delete()
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            if date.weekday() < 5:
                status = "present" if random.random() > 0.1 else "absent"
                a = Attendance(scholar_id=s.id, date=date.date(), status=status)
                db.session.add(a)

    # 3. Add some Publications
    for s in scholars:
        Publication.query.filter_by(scholar_id=s.id).delete()
        p = Publication(
            scholar_id=s.id,
            title=f"Novel approaches in {s.research_area or 'Research %d' % s.id}",
            journal="International Journal of Science",
            status="published",
            year=2024
        )
        db.session.add(p)

    db.session.commit()
    print("Database seeded with fresh student progress data!")
