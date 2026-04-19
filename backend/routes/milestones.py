from flask import Blueprint, request, jsonify
from db import db
from models import Milestone
from datetime import date

milestones_bp = Blueprint('milestones', __name__)


@milestones_bp.route('/<int:scholar_id>', methods=['GET'])
def get_milestones(scholar_id):
    ms = Milestone.query.filter_by(scholar_id=scholar_id).order_by(Milestone.due_date).all()
    return jsonify([_serialize(m) for m in ms])


@milestones_bp.route('/', methods=['POST'])
def create_milestone():
    data = request.get_json()
    m = Milestone(
        scholar_id  = data['scholar_id'],
        title       = data['title'],
        description = data.get('description', ''),
        due_date    = date.fromisoformat(data['due_date']) if data.get('due_date') else None,
        status      = data.get('status', 'pending'),
    )
    db.session.add(m)
    db.session.commit()
    return jsonify({'message': 'Milestone created', 'id': m.id}), 201


@milestones_bp.route('/<int:milestone_id>', methods=['PUT'])
def update_milestone(milestone_id):
    m    = Milestone.query.get_or_404(milestone_id)
    data = request.get_json()
    for field in ['title', 'description', 'status', 'faculty_note']:
        if field in data:
            setattr(m, field, data[field])
    if 'due_date' in data and data['due_date']:
        m.due_date = date.fromisoformat(data['due_date'])
    if data.get('status') == 'completed' and not m.completed_at:
        m.completed_at = date.today()
    db.session.commit()
    return jsonify({'message': 'Milestone updated'})


@milestones_bp.route('/<int:milestone_id>', methods=['DELETE'])
def delete_milestone(milestone_id):
    m = Milestone.query.get_or_404(milestone_id)
    db.session.delete(m)
    db.session.commit()
    return jsonify({'message': 'Deleted'})


def _serialize(m):
    return {
        'id'          : m.id,
        'scholar_id'  : m.scholar_id,
        'title'       : m.title,
        'description' : m.description,
        'due_date'    : str(m.due_date) if m.due_date else None,
        'status'      : m.status,
        'faculty_note': getattr(m, 'faculty_note', None),
        'completed_at': str(m.completed_at) if m.completed_at else None,
        'created_at'  : str(m.created_at),
    }
