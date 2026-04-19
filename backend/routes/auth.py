from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db import db
from models import User, Scholar, Supervisor

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    required = ['email', 'password', 'role']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409

    user = User(
        email         = data['email'].strip().lower(),
        password_hash = generate_password_hash(data['password']),
        role          = data['role']
    )
    db.session.add(user)
    db.session.flush()  # get user.id before commit

    if data['role'] == 'scholar':
        scholar = Scholar(
            user_id       = user.id,
            enrollment_id = data.get('enrollment_id'),
            first_name    = data.get('first_name', ''),
            last_name     = data.get('last_name', ''),
            phone         = data.get('phone', ''),
            gender        = data.get('gender', ''),
            university    = data.get('university', ''),
            department    = data.get('department', ''),
            enroll_year   = data.get('enroll_year'),
            research_area = data.get('research_area', ''),
            fellowship    = data.get('fellowship', ''),
        )
        db.session.add(scholar)

    elif data['role'] == 'supervisor':
        supervisor = Supervisor(
            user_id     = user.id,
            first_name  = data.get('first_name', ''),
            last_name   = data.get('last_name', ''),
            phone       = data.get('phone', ''),
            department  = data.get('department', ''),
            designation = data.get('designation', ''),
            university  = data.get('university', ''),
        )
        db.session.add(supervisor)

    db.session.commit()
    return jsonify({'message': 'Registration successful', 'user_id': user.id}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    raw_id   = data.get('email', '').strip()
    email    = raw_id.lower()
    password = data.get('password', '')
    requested_role = data.get('role', '')

    if not raw_id or not password or not requested_role:
        return jsonify({'error': 'Email/ID, password and role are required'}), 400

    user = None
    if '@' in email:
        if requested_role in ['supervisor', 'faculty']:
            user = User.query.filter(User.email == email, User.role.in_(['supervisor', 'faculty'])).first()
        elif requested_role == 'scholar':
            # Scholar can also log in with their email
            user = User.query.filter_by(email=email, role='scholar').first()
        else:
            user = User.query.filter_by(email=email, role=requested_role).first()
    elif requested_role == 'scholar':
        # Try finding by enrollment_id (case-insensitive variants)
        scholar = Scholar.query.filter(
            (Scholar.enrollment_id == raw_id) | 
            (Scholar.enrollment_id == email) |
            (Scholar.enrollment_id == raw_id.upper())
        ).first()
        if scholar:
            user = scholar.user

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid email/ID or password'}), 401

    if user.status == 'Suspended' and user.suspended_until:
        if datetime.utcnow().replace(tzinfo=None) > user.suspended_until.replace(tzinfo=None):
            user.status = 'Active'
            user.suspended_until = None
            db.session.commit()

    effective_status = user.status or 'Active'
    if effective_status != 'Active':
        msg = f'Your account has been {effective_status.lower()}.'
        if user.status == 'Suspended' and user.suspended_until:
            msg += f' Suspended until {user.suspended_until.strftime("%Y-%m-%d %H:%M")}.'
        return jsonify({'error': msg + ' Please contact support.'}), 403

    # Build profile payload
    profile = {}
    if user.role == 'scholar' and user.scholar:
        s = user.scholar
        profile = {
            'scholar_id'  : s.id,
            'name'        : f"{s.first_name} {s.last_name}".strip(),
            'department'  : s.department,
            'university'  : s.university,
            'enroll_year' : s.enroll_year,
            'fellowship'  : s.fellowship,
        }
    elif user.role in ['supervisor', 'faculty'] and user.supervisor:
        sv = user.supervisor
        profile = {
            'supervisor_id': sv.id,
            'name'         : f"Dr. {sv.first_name} {sv.last_name}".strip(),
            'department'   : sv.department,
            'designation'  : sv.designation,
            'university'   : sv.university,
        }

    # Top-level helpers for frontend
    scholar_id    = profile.get('scholar_id')    if user.role == 'scholar'                       else None
    supervisor_id = profile.get('supervisor_id') if user.role in ['supervisor', 'faculty']       else None
    display_name  = profile.get('name', 'User')

    return jsonify({
        'message'      : 'Login successful',
        'user_id'      : user.id,
        'id'           : user.id,
        'role'         : user.role,
        'name'         : display_name,
        'scholar_id'   : scholar_id,
        'supervisor_id': supervisor_id,
        'profile'      : profile,
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/auth/change-password
# Body: {user_id, old_password, new_password}
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/change-password', methods=['PUT'])
def change_password():
    from werkzeug.security import check_password_hash, generate_password_hash
    data         = request.get_json()
    user_id      = data.get('user_id')
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if not check_password_hash(user.password_hash, old_password):
        return jsonify({'error': 'Current password is incorrect'}), 401
    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({'message': 'Password changed successfully'}), 200

@auth_bp.route('/profile/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    profile = {
        'id': user.id,
        'email': user.email,
        'role': user.role,
        'status': user.status,
        'name': 'Unknown User'
    }
    
    if user.role == 'scholar':
        from models import Scholar, Attendance, Publication
        s = Scholar.query.filter_by(user_id=user.id).first()
        if s:
            # Get Supervisor Info
            sup_name = "Not Assigned"
            if s.supervisor_rel:
                sup_name = f"Dr. {s.supervisor_rel.first_name} {s.supervisor_rel.last_name}"
            
            # Attendance Stats
            total_days = Attendance.query.filter_by(scholar_id=s.id).count()
            present_days = Attendance.query.filter_by(scholar_id=s.id, status='present').count()
            absent_days = total_days - present_days
            att_pct = round((present_days / total_days * 100), 1) if total_days > 0 else 0

            # Publication count
            pub_count = Publication.query.filter_by(scholar_id=s.id).count()

            profile.update({
                'name': f"{s.first_name} {s.last_name}".strip(),
                'department': s.department,
                'phone': s.phone,
                'gender': s.gender,
                'research_focus': s.research_area or s.research_focus if hasattr(s, 'research_area') else getattr(s, 'research_focus', ''),
                'supervisor_name': sup_name,
                'attendance': {
                    'percentage': att_pct,
                    'present': present_days,
                    'absent': absent_days,
                    'total': total_days
                },
                'pub_count': pub_count
            })
    else:
        from models import Supervisor, Scholar, Publication
        s = Supervisor.query.filter_by(user_id=user.id).first()
        if s:
            # For supervisors, count scholars and their cumulative publications
            scholars = Scholar.query.filter_by(supervisor_id=s.id).all()
            scholar_ids = [sch.id for sch in scholars]
            pub_count = Publication.query.filter(Publication.scholar_id.in_(scholar_ids)).count() if scholar_ids else 0

            profile.update({
                'name': f"Dr. {s.first_name} {s.last_name}".strip(),
                'department': s.department,
                'phone': s.phone,
                'gender': getattr(s, 'gender', ''),
                'designation': getattr(s, 'designation', ''),
                'experience': getattr(s, 'experience', ''),
                'specialization': getattr(s, 'specialization', ''),
                'scholar_count': len(scholars),
                'pub_count': pub_count
            })
    
    return jsonify(profile), 200

@auth_bp.route('/account/<int:user_id>', methods=['DELETE'])
def delete_account(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Account deleted successfully'}), 200

