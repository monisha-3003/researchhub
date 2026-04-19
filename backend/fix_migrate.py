from app import app
from db import db
from models import User
from werkzeug.security import generate_password_hash

def apply_fixes():
    with app.app_context():
        print("--- ResearchHub Emergency Patch ---")
        
        # 1. Fix NULL statuses
        print("Patching NULL statuses to 'Active'...")
        db.session.execute(db.text("UPDATE users SET status = 'Active' WHERE status IS NULL"))
        
        # 2. Fix plaintext passwords
        print("Verifying password hashes...")
        users = User.query.all()
        count = 0
        for u in users:
            # If password_hash doesn't look like a hash (lacks method prefix)
            if u.password_hash and not (u.password_hash.startswith('pbkdf2:') or 
                                       u.password_hash.startswith('scrypt:') or 
                                       u.password_hash.startswith('sha256:')):
                print(f"  Re-hashing plaintext password for: {u.email}")
                u.password_hash = generate_password_hash(u.password_hash)
                count += 1
        
        db.session.commit()
        print(f"Successfully re-hashed {count} legacy passwords.")
        print("Database migration and patch complete.")

if __name__ == '__main__':
    apply_fixes()
