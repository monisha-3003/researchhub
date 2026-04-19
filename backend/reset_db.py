from app import app
from db import db
import models

def reset_db():
    with app.app_context():
        print("Disabling foreign key checks...")
        db.session.execute(db.text('SET FOREIGN_KEY_CHECKS = 0;'))
        
        print("Dropping all tables...")
        # Get all table names to drop them manually if needed, or just use drop_all
        db.drop_all()
        
        # Also try to drop tables that might not be in the current models but exist in DB
        tables = db.session.execute(db.text('SHOW TABLES;')).fetchall()
        for table in tables:
            t_name = table[0]
            print(f"Dropping legacy table: {t_name}")
            db.session.execute(db.text(f'DROP TABLE IF EXISTS {t_name};'))

        print("Recreating all tables...")
        db.create_all()
        
        db.session.execute(db.text('SET FOREIGN_KEY_CHECKS = 1;'))
        db.session.commit()
        print("Database reset successfully.")

if __name__ == '__main__':
    reset_db()
