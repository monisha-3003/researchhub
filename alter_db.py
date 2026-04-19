from backend.app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE scholars ADD COLUMN dob VARCHAR(50);"))
        db.session.execute(text("ALTER TABLE scholars ADD COLUMN phone VARCHAR(50);"))
        db.session.execute(text("ALTER TABLE scholars ADD COLUMN gender VARCHAR(50);"))
        db.session.execute(text("ALTER TABLE scholars ADD COLUMN university VARCHAR(255);"))
        db.session.execute(text("ALTER TABLE scholars ADD COLUMN research_area VARCHAR(255);"))
        db.session.execute(text("ALTER TABLE scholars ADD COLUMN supervisor_name VARCHAR(255);"))
        db.session.execute(text("ALTER TABLE scholars ADD COLUMN fellowship_type VARCHAR(255);"))
        db.session.commit()
        print("✅ Gracefully added missing profile columns to scholars table!")
    except Exception as e:
        print(f"Error (maybe columns already exist?): {e}")
