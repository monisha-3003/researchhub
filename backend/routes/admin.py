from flask import Blueprint, jsonify, request
from db import db
from models import User, Scholar, Supervisor, LeaveRequest, Publication, SupervisorRequest, Meeting, Notification
from routes.notifications import push_notification

admin_bp = Blueprint('admin', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/admin/stats  — Dashboard KPIs
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/stats', methods=['GET'])
def admin_stats():
    return jsonify({
        'scholars'        : Scholar.query.count(),
        'faculty'         : Supervisor.query.count(),
        'pending_leaves'  : LeaveRequest.query.filter_by(status='pending').count(),
        'pending_reqs'    : SupervisorRequest.query.filter_by(status='pending').count(),
        'publications'    : Publication.query.count(),
        'pending_pub_reviews': Publication.query.filter_by(status='under_review').count(),
        'total_users'     : User.query.count(),
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/admin/scholars  — All scholars
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/scholars', methods=['GET'])
def admin_scholars():
    scholars = db.session.query(Scholar, User).join(User, Scholar.user_id == User.id).all()
    return jsonify([{
        'id'            : s.id,
        'user_id'       : u.id,
        'name'          : f"{s.first_name} {s.last_name}".strip(),
        'email'         : u.email,
        'enrollment_id' : s.enrollment_id,
        'department'    : s.department,
        'status'        : u.status,
        'suspended_until': u.suspended_until.strftime('%Y-%m-%d %H:%M') if u.suspended_until else None,
        'enroll_year'   : s.enroll_year,
        'thesis_stage'  : s.thesis_stage,
        'fellowship'    : s.fellowship,
    } for s, u in scholars]), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/admin/faculty  — All supervisors
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/faculty', methods=['GET'])
def admin_faculty():
    faculty = db.session.query(Supervisor, User).join(User, Supervisor.user_id == User.id).all()
    return jsonify([{
        'id'          : f.id,
        'user_id'     : u.id,
        'name'        : f"Dr. {f.first_name} {f.last_name}".strip(),
        'email'       : u.email,
        'department'  : f.department,
        'status'      : u.status,
        'suspended_until': u.suspended_until.strftime('%Y-%m-%d %H:%M') if u.suspended_until else None,
        'designation' : f.designation or 'Assistant Professor',
        'scholars'    : Scholar.query.filter_by(supervisor_id=f.id).count(),
    } for f, u in faculty]), 200


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/admin/user/<id>/status  — Activate / Suspend / Debar user
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/user/<int:user_id>/status', methods=['PUT'])
def update_user_status(user_id):
    from datetime import datetime, timedelta
    data = request.json
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    status = data.get('status', 'Active')
    user.status = status
    
    if status == 'Suspended':
        days = int(data.get('days', 0))
        if days > 0:
            user.suspended_until = datetime.utcnow() + timedelta(days=days)
        else:
            user.suspended_until = None # indefinite suspension
    else:
        user.suspended_until = None
        
    db.session.commit()
    return jsonify({'message': f"Status updated to {user.status}"}), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/admin/leave-requests  — All pending leaves
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/leave-requests', methods=['GET'])
def admin_all_leaves():
    status_filter = request.args.get('status', 'pending')
    leaves = LeaveRequest.query.filter_by(status=status_filter).order_by(LeaveRequest.applied_at.desc()).all()
    return jsonify([l.to_dict() for l in leaves]), 200


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/admin/leave-requests/<id>/review
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/leave-requests/<int:leave_id>/review', methods=['PUT'])
def admin_review_leave(leave_id):
    from datetime import datetime
    l    = LeaveRequest.query.get_or_404(leave_id)
    data = request.get_json()
    action = data.get('status', 'approved')
    l.status      = action
    l.reviewed_at = datetime.utcnow()
    db.session.flush()
    scholar = Scholar.query.get(l.scholar_id)
    if scholar:
        emoji = '✅' if action == 'approved' else '❌'
        push_notification(
            user_id    = scholar.user_id,
            message    = f"{emoji} Admin {action} your leave request ({l.from_date} – {l.to_date}).",
            notif_type = 'leave_approval',
            related_id = leave_id,
        )
    db.session.commit()
    return jsonify({'message': f'Leave {action}'}), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/admin/supervisor-requests  — Pending supervisor assignment requests
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/supervisor-requests', methods=['GET'])
def admin_supervisor_requests():
    reqs = SupervisorRequest.query.filter_by(status='pending').order_by(SupervisorRequest.created_at.desc()).all()
    return jsonify([r.to_dict() for r in reqs]), 200


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/admin/supervisor-requests/<id>/approve
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/supervisor-requests/<int:req_id>/approve', methods=['PUT'])
def admin_approve_supervisor_request(req_id):
    from datetime import datetime
    req  = SupervisorRequest.query.get_or_404(req_id)
    data = request.get_json() or {}
    action = data.get('status', 'accepted')
    req.status      = action
    req.reviewed_at = datetime.utcnow()

    if action == 'accepted':
        scholar = Scholar.query.get(req.scholar_id)
        if scholar:
            scholar.supervisor_id = req.supervisor_id

    db.session.flush()
    # Notify both parties
    scholar = Scholar.query.get(req.scholar_id)
    if scholar:
        push_notification(scholar.user_id,
            f"🎓 Admin {action} your supervisor assignment to Dr. {req.supervisor.first_name} {req.supervisor.last_name}.",
            'supervisor_request', req_id)
    push_notification(req.supervisor.user_id,
        f"📋 Admin {action} a supervisor request from a scholar.",
        'supervisor_request', req_id)

    db.session.commit()
    return jsonify({'message': f'Request {action}'}), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/admin/growth-data
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/growth-data', methods=['GET'])
def admin_growth():
    return jsonify({
        'labels'  : ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
        'scholars': [24, 28, 35, 42, 50, 65, 78, 82, 90, 102],
        'faculty' : [8, 10, 12, 12, 15, 18, 20, 22, 25, 28],
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/admin/role-data
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/role-data', methods=['GET'])
def admin_roles():
    scholars = Scholar.query.count()
    faculty  = Supervisor.query.count()
    return jsonify({
        'series': [scholars, faculty, 1],
        'labels': ['Scholars', 'Faculty', 'Admins'],
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/admin/activity-feed  — Unified system event feed
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/activity-feed', methods=['GET'])
def activity_feed():
    limit  = request.args.get('limit', 50, type=int)
    events = []

    # Leave requests (pending)
    leaves = LeaveRequest.query.order_by(LeaveRequest.applied_at.desc()).limit(limit).all()
    for l in leaves:
        events.append({
            'type'     : 'leave',
            'emoji'    : '📋',
            'message'  : f"{l.scholar.first_name} {l.scholar.last_name} submitted a {l.leave_type} leave request ({l.from_date} – {l.to_date})",
            'status'   : l.status,
            'id'       : l.id,
            'timestamp': str(l.applied_at),
        })

    # Supervisor requests (pending)
    sv_reqs = SupervisorRequest.query.order_by(SupervisorRequest.created_at.desc()).limit(limit).all()
    for r in sv_reqs:
        scholar_name  = f"{r.scholar.first_name} {r.scholar.last_name}" if r.scholar else 'Scholar'
        sv_name       = f"Dr. {r.supervisor.first_name} {r.supervisor.last_name}" if r.supervisor else 'Supervisor'
        events.append({
            'type'     : 'supervisor_request',
            'emoji'    : '🎓',
            'message'  : f"{scholar_name} sent a supervisor request to {sv_name}",
            'status'   : r.status,
            'id'       : r.id,
            'timestamp': str(r.created_at),
        })

    # Publications submitted for review
    pubs = Publication.query.filter_by(status='under_review').order_by(Publication.id.desc()).limit(limit).all()
    for p in pubs:
        scholar_name = f"{p.scholar.first_name} {p.scholar.last_name}" if p.scholar else 'Scholar'
        events.append({
            'type'     : 'publication',
            'emoji'    : '📄',
            'message'  : f"{scholar_name} submitted a publication: \"{p.title[:60]}{'...' if len(p.title) > 60 else ''}\"",
            'status'   : p.status,
            'id'       : p.id,
            'timestamp': str(p.id),  # use id as proxy if no created_at
        })

    # Sort by timestamp descending
    events.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(events[:limit]), 200
