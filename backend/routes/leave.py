from flask import Blueprint, request, jsonify
from db import db
from models import LeaveRequest, Scholar, Supervisor
from routes.notifications import push_notification
from datetime import date, datetime

leave_bp = Blueprint('leave', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/leave/<scholar_id>  — Scholar's leave history
# ─────────────────────────────────────────────────────────────────────────────
@leave_bp.route('/<int:scholar_id>', methods=['GET'])
def get_leaves(scholar_id):
    leaves = LeaveRequest.query.filter_by(scholar_id=scholar_id).order_by(LeaveRequest.applied_at.desc()).all()
    return jsonify([l.to_dict() for l in leaves]), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/leave/pending/<supervisor_id>  — Supervisor's pending leaves
# ─────────────────────────────────────────────────────────────────────────────
@leave_bp.route('/pending/<int:supervisor_id>', methods=['GET'])
def get_pending_leaves(supervisor_id):
    scholars = Scholar.query.filter_by(supervisor_id=supervisor_id).all()
    scholar_ids = [s.id for s in scholars]
    leaves = LeaveRequest.query.filter(
        LeaveRequest.scholar_id.in_(scholar_ids),
        LeaveRequest.status == 'pending'
    ).order_by(LeaveRequest.applied_at.desc()).all()
    return jsonify([l.to_dict() for l in leaves]), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/leave/  — Submit a leave request
# ─────────────────────────────────────────────────────────────────────────────
@leave_bp.route('/', methods=['POST'])
def apply_leave():
    data = request.get_json()

    try:
        from_date = date.fromisoformat(data['from_date'])
        to_date   = date.fromisoformat(data['to_date'])
    except (KeyError, ValueError) as e:
        return jsonify({'error': f'Invalid date: {e}'}), 400

    if from_date > to_date:
        return jsonify({'error': 'Start date must be before end date'}), 400

    # Validate date range (max 2 months before start date, max 2 weeks from now to end)
    today = date.today()
    if (today - from_date).days > 60:
        return jsonify({'error': 'Cannot apply for leave more than 2 months in the past'}), 400

    l = LeaveRequest(
        scholar_id    = data['scholar_id'],
        supervisor_id = data.get('supervisor_id'),
        leave_type    = data.get('leave_type', 'Personal'),
        from_date     = from_date,
        to_date       = to_date,
        reason        = data.get('reason', ''),
        submitted_to  = data.get('submitted_to', 'faculty'),
        status        = 'pending',
    )
    db.session.add(l)
    db.session.flush()  # get l.id

    # Notify supervisor
    if data.get('supervisor_id'):
        sv = Supervisor.query.get(data['supervisor_id'])
        if sv:
            scholar = Scholar.query.get(data['scholar_id'])
            scholar_name = f"{scholar.first_name} {scholar.last_name}".strip() if scholar else "A scholar"
            push_notification(
                user_id    = sv.user_id,
                message    = f"📋 {scholar_name} submitted a leave request from {from_date} to {to_date}.",
                notif_type = 'leave_approval',
                related_id = l.id,
            )

    db.session.commit()
    return jsonify({'message': 'Leave request submitted', 'id': l.id}), 201


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/leave/<leave_id>/review  — Approve or Reject (supervisor)
# ─────────────────────────────────────────────────────────────────────────────
@leave_bp.route('/<int:leave_id>/review', methods=['PUT'])
def review_leave(leave_id):
    l    = LeaveRequest.query.get_or_404(leave_id)
    data = request.get_json()
    action = data.get('status', 'approved')

    l.status          = action
    l.supervisor_note = data.get('note', '')
    l.reviewed_at     = datetime.utcnow()
    db.session.flush()

    # Notify scholar
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
# GET /api/leave/all  — Admin: all leaves
# ─────────────────────────────────────────────────────────────────────────────
@leave_bp.route('/all', methods=['GET'])
def get_all_leaves():
    status_filter = request.args.get('status')
    q = LeaveRequest.query
    if status_filter:
        q = q.filter_by(status=status_filter)
    leaves = q.order_by(LeaveRequest.applied_at.desc()).all()
    return jsonify([l.to_dict() for l in leaves]), 200
