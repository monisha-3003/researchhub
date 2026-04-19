from flask import Blueprint, request, jsonify
from db import db
from models import Scholar, User, Supervisor, SupervisorRequest
from routes.notifications import push_notification

scholar_bp = Blueprint('scholar', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/scholar/<scholar_id> or /api/scholar/profile/<scholar_id>
@scholar_bp.route('/<int:scholar_id>', methods=['GET'])
@scholar_bp.route('/profile/<int:scholar_id>', methods=['GET'])
def get_scholar(scholar_id):
    s  = Scholar.query.get_or_404(scholar_id)
    sv = Supervisor.query.get(s.supervisor_id) if s.supervisor_id else None
    u  = User.query.get(s.user_id)
    return jsonify({
        'id'              : s.id,
        'user_id'         : s.user_id,
        'email'           : u.email if u else None,
        'enrollment_id'   : s.enrollment_id,
        'first_name'      : s.first_name,
        'last_name'       : s.last_name,
        'name'            : f"{s.first_name} {s.last_name}".strip(),
        'phone'           : s.phone,
        'dob'             : str(s.dob) if s.dob else None,
        'gender'          : s.gender,
        'address'         : s.address,
        'university'      : s.university,
        'department'      : s.department,
        'enroll_year'     : s.enroll_year,
        'research_area'   : s.research_area,
        'fellowship'      : s.fellowship,
        'progress_pct'    : s.progress_pct,
        'thesis_stage'    : s.thesis_stage,
        'supervisor_id'   : s.supervisor_id,
        'supervisor_name' : f"Dr. {sv.first_name} {sv.last_name}" if sv else None,
        'supervisor_user_id': sv.user_id if sv else None,
        'supervisor_dept' : sv.department if sv else None,
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/scholar/<scholar_id> or /api/scholar/profile/<scholar_id>
@scholar_bp.route('/<int:scholar_id>', methods=['PUT'])
@scholar_bp.route('/profile/<int:scholar_id>', methods=['PUT'])
def update_scholar(scholar_id):
    s    = Scholar.query.get_or_404(scholar_id)
    data = request.get_json()
    for field in ['first_name', 'last_name', 'phone', 'gender',
                  'university', 'department', 'research_area',
                  'fellowship', 'thesis_stage', 'address']:
        if field in data:
            setattr(s, field, data[field])
    if 'dob' in data and data['dob']:
        from datetime import date
        s.dob = date.fromisoformat(data['dob'])
    db.session.commit()
    return jsonify({'message': 'Profile updated'}), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/scholar/by-supervisor/<supervisor_id>
# ─────────────────────────────────────────────────────────────────────────────
@scholar_bp.route('/by-supervisor/<int:supervisor_id>', methods=['GET'])
def get_scholars_by_supervisor(supervisor_id):
    scholars = Scholar.query.filter_by(supervisor_id=supervisor_id).all()
    return jsonify([{
        'id'           : s.id,
        'name'         : f"{s.first_name} {s.last_name}".strip(),
        'department'   : s.department,
        'enroll_year'  : s.enroll_year,
        'research_area': s.research_area,
        'progress_pct' : s.progress_pct,
        'thesis_stage' : s.thesis_stage,
        'fellowship'   : s.fellowship,
    } for s in scholars]), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/scholar/request-supervisor  — Send supervisor request
# ─────────────────────────────────────────────────────────────────────────────
@scholar_bp.route('/request-supervisor', methods=['POST'])
def request_supervisor():
    data = request.get_json()
    scholar_id    = data.get('scholar_id')
    supervisor_id = data.get('supervisor_id')

    if not scholar_id or not supervisor_id:
        return jsonify({'error': 'scholar_id and supervisor_id required'}), 400

    existing = SupervisorRequest.query.filter_by(
        scholar_id=scholar_id, supervisor_id=supervisor_id
    ).filter(SupervisorRequest.status.in_(['pending', 'accepted'])).first()

    if existing:
        return jsonify({'error': 'Request already sent or accepted'}), 409

    req = SupervisorRequest(scholar_id=scholar_id, supervisor_id=supervisor_id)
    db.session.add(req)
    db.session.flush()

    sv      = Supervisor.query.get(supervisor_id)
    scholar = Scholar.query.get(scholar_id)
    if sv and scholar:
        push_notification(
            user_id    = sv.user_id,
            message    = f"🎓 {scholar.first_name} {scholar.last_name} sent you a supervisor request.",
            notif_type = 'supervisor_request',
            related_id = req.id,
        )
    db.session.commit()
    return jsonify({'message': 'Request sent', 'id': req.id}), 201


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/scholar/<scholar_id>/supervisor-request  — Check my request status
# ─────────────────────────────────────────────────────────────────────────────
@scholar_bp.route('/<int:scholar_id>/supervisor-request', methods=['GET'])
def get_supervisor_request_status(scholar_id):
    reqs = SupervisorRequest.query.filter_by(scholar_id=scholar_id).order_by(SupervisorRequest.created_at.desc()).all()
    return jsonify([r.to_dict() for r in reqs]), 200
