from flask import Blueprint, request, jsonify
from db import db
from models import Message

messages_bp = Blueprint('messages', __name__)


@messages_bp.route('/conversation', methods=['GET'])
def get_conversation():
    user1 = request.args.get('user1', type=int)
    user2 = request.args.get('user2', type=int)
    msgs  = Message.query.filter(
        ((Message.sender_id == user1) & (Message.receiver_id == user2)) |
        ((Message.sender_id == user2) & (Message.receiver_id == user1))
    ).order_by(Message.sent_at.asc()).all()

    # Mark received messages as read
    for m in msgs:
        if m.receiver_id == user1 and not m.is_read:
            m.is_read = True
    db.session.commit()

    return jsonify([_serialize(m) for m in msgs])


@messages_bp.route('/', methods=['POST'])
def send_message():
    from routes.notifications import push_notification
    data = request.get_json()
    m = Message(
        sender_id   = data['sender_id'],
        receiver_id = data['receiver_id'],
        content     = data['content'],
    )
    db.session.add(m)
    db.session.flush()
    
    # Notify Receiver
    push_notification(
        user_id    = data['receiver_id'],
        message    = f"💬 New message: \"{data['content'][:40]}...\"",
        notif_type = 'message',
        related_id = m.id
    )
    
    db.session.commit()
    return jsonify({'message': 'Message sent', 'id': m.id}), 201


@messages_bp.route('/unread/<int:user_id>', methods=['GET'])
def unread_count(user_id):
    count = Message.query.filter_by(receiver_id=user_id, is_read=False).count()
    return jsonify({'unread': count})


@messages_bp.route('/conversations-list/<int:user_id>', methods=['GET'])
def list_conversations(user_id):
    from models import User, Scholar, Supervisor
    # Find all unique users who sent to or received from user_id
    msgs = Message.query.filter((Message.sender_id == user_id) | (Message.receiver_id == user_id)).order_by(Message.sent_at.desc()).all()
    
    seen = set()
    result = []
    
    for m in msgs:
        other_id = m.receiver_id if m.sender_id == user_id else m.sender_id
        if other_id not in seen:
            seen.add(other_id)
            u = User.query.get(other_id)
            name = "System"
            dept = "ResearchHub"
            
            if u.role == 'scholar':
                s = Scholar.query.filter_by(user_id=u.id).first()
                if s: 
                    name = f"{s.first_name} {s.last_name}"
                    dept = s.department
            elif u.role == 'supervisor' or u.role == 'faculty':
                sv = Supervisor.query.filter_by(user_id=u.id).first()
                if sv:
                    name = f"Dr. {sv.first_name} {sv.last_name}"
                    dept = sv.department

            result.append({
                'user_id': u.id,
                'name': name,
                'role': u.role,
                'department': dept,
                'last_message': m.content,
                'timestamp': str(m.sent_at),
                'unread': Message.query.filter_by(sender_id=u.id, receiver_id=user_id, is_read=False).count()
            })
            
    return jsonify(result)


@messages_bp.route('/available-recipients/<int:user_id>', methods=['GET'])
def available_recipients(user_id):
    from models import User, Scholar, Supervisor
    me = User.query.get(user_id)
    if not me:
        return jsonify([])

    recipients = []
    
    # If I am a scholar, I can message any faculty member
    if me.role == 'scholar':
        faculties = Supervisor.query.all()
        for f in faculties:
            recipients.append({
                'id': f.user_id,
                'user_id': f.user_id,
                'name': f"Dr. {f.first_name} {f.last_name}",
                'role': 'faculty',
                'department': f.department
            })
            
    # If I am a faculty member, I can message any scholar
    elif me.role in ['faculty', 'supervisor']:
        scholars = Scholar.query.all()
        for s in scholars:
            recipients.append({
                'id': s.user_id,
                'user_id': s.user_id,
                'name': f"{s.first_name} {s.last_name}",
                'role': 'scholar',
                'department': s.department
            })
            
    return jsonify(recipients)


def _serialize(m):
    return {
        'id'         : m.id,
        'sender_id'  : m.sender_id,
        'receiver_id': m.receiver_id,
        'content'    : m.content,
        'is_read'    : m.is_read,
        'sent_at'    : str(m.sent_at),
    }
