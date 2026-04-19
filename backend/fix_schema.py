import sys, os
from app import app, db
from sqlalchemy import text

with app.app_context():
    print("Checking and fixing database schema...")
    try:
        # Check if 'faculty_note' exists in milestones
        db.session.execute(text("ALTER TABLE milestones ADD COLUMN faculty_note TEXT NULL"))
        print("Added 'faculty_note' column to milestones.")
    except Exception as e:
        if "Duplicate column name" in str(e) or "1060" in str(e):
            print("'faculty_note' already exists.")
        else:
            print(f"Error adding faculty_note: {e}")

    try:
        # Check for research_area in scholars
        db.session.execute(text("ALTER TABLE scholars ADD COLUMN research_area VARCHAR(255) NULL"))
        print("Added 'research_area' column to scholars.")
    except Exception as e:
        if "Duplicate column name" in str(e) or "1060" in str(e):
            print("'research_area' already exists.")
        else:
            print(f"Error adding research_area: {e}")

    db.session.commit()
    print("Database schema updated successfully.")
