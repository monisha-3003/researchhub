from flask import Flask
from flask_cors import CORS
from db import db
from routes.auth import auth_bp
from routes.scholar import scholar_bp
from routes.supervisor import supervisor_bp
from routes.milestones import milestones_bp
from routes.documents import documents_bp
from routes.publications import publications_bp
from routes.stipend import stipend_bp
from routes.leave import leave_bp
from routes.messages import messages_bp
from routes.meetings import meetings_bp
from routes.admin import admin_bp
from routes.attendance import attendance_bp
from routes.notifications import notifications_bp
import os

app = Flask(__name__)
CORS(app)

# ── MySQL Config ──────────────────────────────────────────────────────────────
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mysql+mysqlconnector://root:lrhbSJbnfSzjwbvgaGWUYoAtFDnBnkni'
    '@mysql.railway.internal:3306/railway'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')

# ── THIS WAS MISSING ──────────────────────────────────────────────────────────
db.init_app(app)

# ── Register Blueprints ───────────────────────────────────────────────────────
app.register_blueprint(auth_bp,          url_prefix='/api/auth')
app.register_blueprint(scholar_bp,       url_prefix='/api/scholar')
app.register_blueprint(supervisor_bp,    url_prefix='/api/supervisor')
app.register_blueprint(milestones_bp,    url_prefix='/api/milestones')
app.register_blueprint(documents_bp,     url_prefix='/api/documents')
app.register_blueprint(publications_bp,  url_prefix='/api/publications')
app.register_blueprint(stipend_bp,       url_prefix='/api/stipend')
app.register_blueprint(leave_bp,         url_prefix='/api/leave')
app.register_blueprint(messages_bp,      url_prefix='/api/messages')
app.register_blueprint(meetings_bp,      url_prefix='/api/meetings')
app.register_blueprint(admin_bp,         url_prefix='/api/admin')
app.register_blueprint(attendance_bp,    url_prefix='/api/attendance')
app.register_blueprint(notifications_bp, url_prefix='/api/notifications')

# ── Create all tables on first run ───────────────────────────────────────────
with app.app_context():
    db.create_all()
    print("SUCCESS: All tables created successfully.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)