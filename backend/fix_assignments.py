import sys, os
from app import app
from models import Scholar, db

with app.app_context():
    # Assign all scholars to Dr. Dany Thomas (Supervisor ID=1)
    # This ensures that when logged in as Dany, you see all the data
    affected = Scholar.query.update({Scholar.supervisor_id: 1})
    db.session.commit()
    print(f"Successfully reassigned {affected} scholars to Dr. Dany Thomas.")
