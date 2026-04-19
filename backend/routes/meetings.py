from flask import Blueprint, request, jsonify
from db import db
from models import Meeting
from datetime import datetime

meetings_bp = Blueprint('meetings', __name__)


@meetings_bp.route('/scholar/<int:scholar_id>', methods=['GET'])
def get_scholar_meetings(scholar_id):
    meetings = Meeting.query.filter_by(scholar_id=scholar_id).order_by(Meeting.scheduled_at.desc()).all()
    return jsonify([_serialize(m) for m in meetings])


@meetings_bp.route('/supervisor/<int:supervisor_id>', methods=['GET'])
def get_supervisor_meetings(supervisor_id):
    meetings = Meeting.query.filter_by(supervisor_id=supervisor_id).order_by(Meeting.scheduled_at.asc()).all()
    result = []
    for m in meetings:
        from models import Scholar
        s = Scholar.query.get(m.scholar_id)
        d = _serialize(m)
        d['scholar_name'] = f"{s.first_name} {s.last_name}".strip() if s else ''
        result.append(d)
    return jsonify(result)


@meetings_bp.route('/', methods=['POST'])
def schedule_meeting():
    data = request.get_json()
    m = Meeting(
        scholar_id    = data['scholar_id'],
        supervisor_id = data['supervisor_id'],
        title         = data.get('title', 'Review Meeting'),
        scheduled_at  = datetime.fromisoformat(data['scheduled_at']),
        notes         = data.get('notes', ''),
        status        = 'scheduled',
    )
    db.session.add(m)
    db.session.commit()
    return jsonify({'message': 'Meeting scheduled', 'id': m.id}), 201


@meetings_bp.route('/<int:meeting_id>', methods=['PUT'])
def update_meeting(meeting_id):
    m    = Meeting.query.get_or_404(meeting_id)
    data = request.get_json()
    for field in ['title', 'notes', 'status']:
        if field in data:
            setattr(m, field, data[field])
    if 'scheduled_at' in data:
        m.scheduled_at = datetime.fromisoformat(data['scheduled_at'])
    db.session.commit()
    return jsonify({'message': 'Meeting updated'})


def _serialize(m):
    return {
        'id'           : m.id,
        'scholar_id'   : m.scholar_id,
        'supervisor_id': m.supervisor_id,
        'title'        : m.title,
        'scheduled_at' : str(m.scheduled_at),
        'notes'        : m.notes,
        'status'       : m.status,
        'created_at'   : str(m.created_at),
    }
