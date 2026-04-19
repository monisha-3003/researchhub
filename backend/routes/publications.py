from flask import Blueprint, request, jsonify
from db import db
from models import Publication

publications_bp = Blueprint('publications', __name__)


@publications_bp.route('/<int:scholar_id>', methods=['GET'])
def get_publications(scholar_id):
    pubs = Publication.query.filter_by(scholar_id=scholar_id).order_by(Publication.year.desc()).all()
    return jsonify([_serialize(p) for p in pubs])


@publications_bp.route('/', methods=['POST'])
def create_publication():
    data = request.get_json()
    p = Publication(
        scholar_id = data['scholar_id'],
        title      = data['title'],
        venue      = data.get('venue', ''),
        pub_type   = data.get('pub_type', ''),
        year       = data.get('year'),
        doi        = data.get('doi', ''),
        status     = data.get('status', 'under_review'),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'message': 'Publication added', 'id': p.id}), 201


@publications_bp.route('/<int:pub_id>', methods=['PUT'])
def update_publication(pub_id):
    p    = Publication.query.get_or_404(pub_id)
    data = request.get_json()
    for field in ['title', 'venue', 'pub_type', 'year', 'doi', 'status']:
        if field in data:
            setattr(p, field, data[field])
    db.session.commit()
    return jsonify({'message': 'Publication updated'})


@publications_bp.route('/<int:pub_id>', methods=['DELETE'])
def delete_publication(pub_id):
    p = Publication.query.get_or_404(pub_id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'message': 'Deleted'})


def _serialize(p):
    return {
        'id'        : p.id,
        'scholar_id': p.scholar_id,
        'title'     : p.title,
        'venue'     : p.venue,
        'pub_type'  : p.pub_type,
        'year'      : p.year,
        'doi'       : p.doi,
        'status'    : p.status,
        'created_at': str(p.created_at),
    }
