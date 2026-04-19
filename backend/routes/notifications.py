from flask import Blueprint, request, jsonify
from db import db
from models import Notification

notifications_bp = Blueprint('notifications', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/notifications/<user_id>
# Returns all notifications + unread count for a user
# ─────────────────────────────────────────────────────────────────────────────
@notifications_bp.route('/<int:user_id>', methods=['GET'])
def get_notifications(user_id):
    try:
        notifications = (
            Notification.query
            .filter_by(user_id=user_id)
            .order_by(Notification.created_at.desc())
            .limit(50)
            .all()
        )
        unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        return jsonify({
            'notifications': [n.to_dict() for n in notifications],
            'unread_count' : unread_count,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/notifications/<id>/read
# Mark a single notification as read
# ─────────────────────────────────────────────────────────────────────────────
@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
def mark_read(notification_id):
    notif = Notification.query.get(notification_id)
    if not notif:
        return jsonify({'error': 'Notification not found'}), 404
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True}), 200


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/notifications/read-all/<user_id>
# Mark ALL notifications as read for a user
# ─────────────────────────────────────────────────────────────────────────────
@notifications_bp.route('/read-all/<int:user_id>', methods=['PUT'])
def mark_all_read(user_id):
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True}), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/notifications/
# Internal: create a notification
# ─────────────────────────────────────────────────────────────────────────────
@notifications_bp.route('/', methods=['POST'])
def create_notification():
    try:
        data = request.get_json()
        notif = Notification(
            user_id    = data['user_id'],
            message    = data['message'],
            type       = data['type'],
            related_id = data.get('related_id'),
        )
        db.session.add(notif)
        db.session.commit()
        return jsonify({'id': notif.id}), 201
    except KeyError as e:
        return jsonify({'error': f'Missing field: {e}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPER — used by other routes to fire notifications
# ─────────────────────────────────────────────────────────────────────────────
def push_notification(user_id, message, notif_type, related_id=None):
    """Create a notification without an HTTP call. Call from other route files."""
    n = Notification(
        user_id    = user_id,
        message    = message,
        type       = notif_type,
        related_id = related_id,
    )
    db.session.add(n)
    # Caller is responsible for db.session.commit()
