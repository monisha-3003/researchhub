from flask import Blueprint, request, jsonify
from db import db
from models import Supervisor, Scholar, LeaveRequest, Publication, Meeting, SupervisorRequest
from routes.notifications import push_notification
from datetime import datetime

supervisor_bp = Blueprint('supervisor', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/supervisor/<id>
# ─────────────────────────────────────────────────────────────────────────────
@supervisor_bp.route('/<int:supervisor_id>', methods=['GET'])
def get_supervisor(supervisor_id):
    sv = Supervisor.query.get_or_404(supervisor_id)
    return jsonify({
        'id'            : sv.id,
        'user_id'       : sv.user_id,
        'first_name'    : sv.first_name,
        'last_name'     : sv.last_name,
        'name'          : f"Dr. {sv.first_name} {sv.last_name}".strip(),
        'phone'         : sv.phone,
        'department'    : sv.department,
        'designation'   : sv.designation,
        'university'    : sv.university,
        'specialization': sv.specialization,
        'office_room'   : sv.office_room,
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/supervisor/<id>
# ─────────────────────────────────────────────────────────────────────────────
@supervisor_bp.route('/<int:supervisor_id>', methods=['PUT'])
def update_supervisor(supervisor_id):
    sv   = Supervisor.query.get_or_404(supervisor_id)
    data = request.get_json()
    for field in ['first_name', 'last_name', 'phone', 'department',
                  'designation', 'university', 'specialization', 'office_room']:
        if field in data:
            setattr(sv, field, data[field])
    db.session.commit()
    return jsonify({'message': 'Profile updated'}), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/supervisor/all  — for faculty directory
# ─────────────────────────────────────────────────────────────────────────────
@supervisor_bp.route('/all', methods=['GET'])
def list_supervisors():
    from models import User
    supervisors = Supervisor.query.all()
    result = []
    for sv in supervisors:
        u = User.query.get(sv.user_id)
        result.append({
            'id'            : sv.id,
            'user_id'       : sv.user_id,
            'name'          : f"Dr. {sv.first_name} {sv.last_name}".strip(),
            'email'         : u.email if u else '',
            'department'    : sv.department,
            'designation'   : sv.designation,
            'university'    : sv.university,
            'specialization': sv.specialization,
            'office_room'   : sv.office_room,
            'scholars_count': Scholar.query.filter_by(supervisor_id=sv.id).count(),
        })
    return jsonify(result), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/supervisor/<id>/scholars  — my scholars
# ─────────────────────────────────────────────────────────────────────────────
@supervisor_bp.route('/<int:supervisor_id>/scholars', methods=['GET'])
def get_my_scholars(supervisor_id):
    scholars = Scholar.query.filter_by(supervisor_id=supervisor_id).all()
    result = []
    for s in scholars:
        from models import User
        u = User.query.get(s.user_id)
        # Count milestones
        from models import Milestone
        total_ms = Milestone.query.filter_by(scholar_id=s.id).count()
        done_ms  = Milestone.query.filter_by(scholar_id=s.id, status='completed').count()
        result.append({
            'id'              : s.id,
            'user_id'         : s.user_id,
            'name'            : f"{s.first_name} {s.last_name}".strip(),
            'email'           : u.email if u else '',
            'department'      : s.department,
            'enrollment_id'   : s.enrollment_id,
            'enroll_year'     : s.enroll_year,
            'research_area'   : s.research_area,
            'fellowship'      : s.fellowship,
            'thesis_stage'    : s.thesis_stage,
            'progress_pct'    : s.progress_pct,
            'milestones_done' : done_ms,
            'milestones_total': total_ms,
        })
    return jsonify(result), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/supervisor/<id>/leave-requests  — pending leaves from my scholars
# ─────────────────────────────────────────────────────────────────────────────
@supervisor_bp.route('/<int:supervisor_id>/leave-requests', methods=['GET'])
def get_leave_requests(supervisor_id):
    scholars    = Scholar.query.filter_by(supervisor_id=supervisor_id).all()
    scholar_ids = [s.id for s in scholars]
    status_filter = request.args.get('status', 'pending')
    is_all = request.args.get('all', '0') == '1'
    
    query = LeaveRequest.query.filter(LeaveRequest.scholar_id.in_(scholar_ids))
    if not is_all:
        query = query.filter(LeaveRequest.status == status_filter)
        
    leaves = query.order_by(LeaveRequest.applied_at.desc()).all()
    return jsonify([l.to_dict() for l in leaves]), 200


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/supervisor/leave/<leave_id>/review  — approve or reject
# ─────────────────────────────────────────────────────────────────────────────
@supervisor_bp.route('/leave/<int:leave_id>/review', methods=['PUT'])
def review_leave(leave_id):
    l    = LeaveRequest.query.get_or_404(leave_id)
    data = request.get_json()
    action = data.get('status', 'approved')
    l.status          = action
    l.supervisor_note = data.get('note', '')
    l.reviewed_at     = datetime.utcnow()
    db.session.flush()

    scholar = Scholar.query.get(l.scholar_id)
    if scholar:
        emoji = '✅' if action == 'approved' else '❌'
        push_notification(
            user_id    = scholar.user_id,
            message    = f"{emoji} Your leave request ({l.from_date} – {l.to_date}) was {action}.",
            notif_type = 'leave_approval',
            related_id = leave_id,
        )
    db.session.commit()
    return jsonify({'message': f'Leave {action}'}), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/supervisor/<id>/publications  — publications pending approval
# ─────────────────────────────────────────────────────────────────────────────
@supervisor_bp.route('/<int:supervisor_id>/publications', methods=['GET'])
def get_pending_publications(supervisor_id):
    scholars    = Scholar.query.filter_by(supervisor_id=supervisor_id).all()
    scholar_ids = [s.id for s in scholars]
    
    status_filter = request.args.get('status', 'under_review')
    is_all = request.args.get('all', '0') == '1'
    
    query = Publication.query.filter(Publication.scholar_id.in_(scholar_ids))
    if not is_all:
        query = query.filter(Publication.status == status_filter)
        
    pubs = query.order_by(Publication.created_at.desc()).all()
    
    result = []
    for p in pubs:
        d = p.to_dict()
        if p.scholar:
            d['scholar_name'] = f"{p.scholar.first_name} {p.scholar.last_name}".strip()
            d['scholar_initials'] = d['scholar_name'].split(' ')[0][0] + d['scholar_name'].split(' ')[-1][0] if ' ' in d['scholar_name'] else d['scholar_name'][:2]
        result.append(d)
        
    return jsonify(result), 200


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/supervisor/publication/<pub_id>/approve  — approve a publication
# ─────────────────────────────────────────────────────────────────────────────
@supervisor_bp.route('/publication/<int:pub_id>/approve', methods=['PUT'])
def approve_publication(pub_id):
    data = request.get_json() or {}
    pub  = Publication.query.get_or_404(pub_id)
    pub.status = data.get('status', 'approved')
    db.session.flush()

    scholar = Scholar.query.get(pub.scholar_id)
    if scholar:
        emoji = '✅' if pub.status == 'approved' else '❌'
        push_notification(
            user_id    = scholar.user_id,
            message    = f"{emoji} Your publication '{pub.title[:60]}' was {pub.status}.",
            notif_type = 'publication',
            related_id = pub_id,
        )
    db.session.commit()
    return jsonify({'message': f'Publication {pub.status}'}), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/supervisor/meetings  — schedule a meeting
# ─────────────────────────────────────────────────────────────────────────────
@supervisor_bp.route('/meetings', methods=['POST'])
def schedule_meeting():
    data = request.get_json()
    try:
        scheduled_at = datetime.fromisoformat(data['scheduled_at'])
    except (KeyError, ValueError):
        return jsonify({'error': 'Invalid scheduled_at datetime'}), 400

    m = Meeting(
        scholar_id    = data['scholar_id'],
        supervisor_id = data['supervisor_id'],
        title         = data.get('title', 'Review Meeting'),
        scheduled_at  = scheduled_at,
        notes         = data.get('notes', ''),
        status        = 'scheduled',
    )
    db.session.add(m)
    db.session.flush()

    scholar = Scholar.query.get(data['scholar_id'])
    if scholar:
        push_notification(
            user_id    = scholar.user_id,
            message    = f"📅 Meeting '{m.title}' scheduled for {scheduled_at.strftime('%b %d, %Y %I:%M %p')}.",
            notif_type = 'meeting',
            related_id = m.id,
        )
    db.session.commit()
    return jsonify({'message': 'Meeting scheduled', 'id': m.id}), 201


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/supervisor/<id>/supervisor-requests  — see incoming scholar requests
# ─────────────────────────────────────────────────────────────────────────────
@supervisor_bp.route('/<int:supervisor_id>/supervisor-requests', methods=['GET'])
def get_supervisor_requests(supervisor_id):
    reqs = SupervisorRequest.query.filter_by(supervisor_id=supervisor_id, status='pending').all()
    return jsonify([r.to_dict() for r in reqs]), 200


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/supervisor/supervisor-requests/<id>/respond
# ─────────────────────────────────────────────────────────────────────────────
@supervisor_bp.route('/supervisor-requests/<int:req_id>/respond', methods=['PUT'])
def respond_to_request(req_id):
    req  = SupervisorRequest.query.get_or_404(req_id)
    data = request.get_json()
    action = data.get('status', 'accepted')
    req.status      = action
    req.reviewed_at = datetime.utcnow()

    # If accepted, assign supervisor_id on scholar record
    if action == 'accepted':
        scholar = Scholar.query.get(req.scholar_id)
        if scholar:
            scholar.supervisor_id = req.supervisor_id

    db.session.flush()

    # Notify scholar
    scholar = Scholar.query.get(req.scholar_id)
    if scholar:
        emoji = '🎓' if action == 'accepted' else '❌'
        push_notification(
            user_id    = scholar.user_id,
            message    = f"{emoji} Your supervisor request was {action} by Dr. {req.supervisor.first_name} {req.supervisor.last_name}.",
            notif_type = 'supervisor_request',
            related_id = req_id,
        )

    db.session.commit()
    return jsonify({'message': f'Request {action}'}), 200
