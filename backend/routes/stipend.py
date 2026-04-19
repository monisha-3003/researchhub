from flask import Blueprint, request, jsonify
from db import db
from models import Stipend
from datetime import date

stipend_bp = Blueprint('stipend', __name__)


@stipend_bp.route('/<int:scholar_id>', methods=['GET'])
def get_stipends(scholar_id):
    records = Stipend.query.filter_by(scholar_id=scholar_id).order_by(Stipend.year.desc(), Stipend.month).all()
    return jsonify([_serialize(s) for s in records])


@stipend_bp.route('/', methods=['POST'])
def add_stipend():
    data = request.get_json()
    s = Stipend(
        scholar_id = data['scholar_id'],
        month      = data['month'],
        year       = data['year'],
        amount     = data['amount'],
        fellowship = data.get('fellowship', ''),
        status     = data.get('status', 'pending'),
        paid_on    = date.fromisoformat(data['paid_on']) if data.get('paid_on') else None,
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({'message': 'Stipend record added', 'id': s.id}), 201


@stipend_bp.route('/<int:stipend_id>', methods=['PUT'])
def update_stipend(stipend_id):
    s    = Stipend.query.get_or_404(stipend_id)
    data = request.get_json()
    for field in ['month', 'year', 'amount', 'fellowship', 'status']:
        if field in data:
            setattr(s, field, data[field])
    if 'paid_on' in data and data['paid_on']:
        s.paid_on = date.fromisoformat(data['paid_on'])
    db.session.commit()
    return jsonify({'message': 'Updated'})


def _serialize(s):
    return {
        'id'        : s.id,
        'scholar_id': s.scholar_id,
        'month'     : s.month,
        'year'      : s.year,
        'amount'    : s.amount,
        'fellowship': s.fellowship,
        'status'    : s.status,
        'paid_on'   : str(s.paid_on) if s.paid_on else None,
    }
