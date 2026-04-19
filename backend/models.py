from db import db
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────────────────────
def _relative_time(dt):
    """Return a human-readable relative time string like '2 hours ago'."""
    if not dt:
        return ''
    now = datetime.utcnow()
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        m = seconds // 60
        return f"{m} minute{'s' if m > 1 else ''} ago"
    elif seconds < 86400:
        h = seconds // 3600
        return f"{h} hour{'s' if h > 1 else ''} ago"
    elif seconds < 604800:
        d = seconds // 86400
        return f"{d} day{'s' if d > 1 else ''} ago"
    else:
        return dt.strftime('%b %d, %Y')


# ─────────────────────────────────────────────────────────────────────────────
# CORE AUTH MODELS
# ─────────────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.Enum('scholar', 'supervisor', 'faculty', 'admin', 'coordinator'), nullable=False)
    status          = db.Column(db.String(50), default='Active', server_default='Active', nullable=False)  # Active, Suspended, Debarred
    suspended_until = db.Column(db.DateTime, nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    scholar    = db.relationship('Scholar',    backref='user', uselist=False)
    supervisor = db.relationship('Supervisor', backref='user', uselist=False)
    notifications = db.relationship('Notification', backref='user', lazy='dynamic',
                                    foreign_keys='Notification.user_id')

    @property
    def display_name(self):
        """Compute display name from profile tables."""
        if self.scholar:
            return f"{self.scholar.first_name} {self.scholar.last_name}".strip()
        if self.supervisor:
            return f"{self.supervisor.first_name} {self.supervisor.last_name}".strip()
        return self.email or 'User'

    def to_dict(self):
        profile = {}
        if self.scholar:
            s = self.scholar
            profile = {
                'scholar_id' : s.id,
                'department' : s.department,
                'university' : s.university,
                'enroll_year': s.enroll_year,
                'fellowship' : s.fellowship,
                'research_area': s.research_area,
            }
        elif self.supervisor:
            sv = self.supervisor
            profile = {
                'supervisor_id': sv.id,
                'department'   : sv.department,
                'university'   : sv.university,
                'designation'  : sv.designation,
            }
        return {
            'id'        : self.id,
            'email'     : self.email,
            'name'      : self.display_name,
            'role'      : self.role,
            'status'    : self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            **profile
        }


# ─────────────────────────────────────────────────────────────────────────────
# PROFILE MODELS
# ─────────────────────────────────────────────────────────────────────────────
class Scholar(db.Model):
    __tablename__ = 'scholars'
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrollment_id = db.Column(db.String(50), unique=True, nullable=True)
    first_name    = db.Column(db.String(80))
    last_name     = db.Column(db.String(80))
    phone         = db.Column(db.String(15))
    dob           = db.Column(db.Date)
    gender        = db.Column(db.String(20))
    university    = db.Column(db.String(150))
    department    = db.Column(db.String(100))
    enroll_year   = db.Column(db.Integer)
    research_area = db.Column(db.String(200))
    fellowship    = db.Column(db.String(100))
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisors.id'), nullable=True)
    progress_pct  = db.Column(db.Integer, default=0)
    thesis_stage  = db.Column(db.String(50), default='Coursework')
    address       = db.Column(db.String(500))
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Supervisor(db.Model):
    __tablename__ = 'supervisors'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    first_name   = db.Column(db.String(80))
    last_name    = db.Column(db.String(80))
    phone        = db.Column(db.String(15))
    department   = db.Column(db.String(100))
    designation  = db.Column(db.String(100))
    university   = db.Column(db.String(150))
    specialization = db.Column(db.String(200))
    office_room  = db.Column(db.String(50))

    scholars     = db.relationship('Scholar', backref='supervisor_rel',
                                   foreign_keys=[Scholar.supervisor_id])


# ─────────────────────────────────────────────────────────────────────────────
# SUPERVISOR REQUEST (Scholar → Faculty)
# ─────────────────────────────────────────────────────────────────────────────
class SupervisorRequest(db.Model):
    __tablename__ = 'supervisor_requests'
    id          = db.Column(db.Integer, primary_key=True)
    scholar_id  = db.Column(db.Integer, db.ForeignKey('scholars.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisors.id'), nullable=False)
    status      = db.Column(db.Enum('pending', 'accepted', 'rejected'), default='pending')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    scholar    = db.relationship('Scholar',    backref='supervisor_requests_sent',    foreign_keys=[scholar_id])
    supervisor = db.relationship('Supervisor', backref='supervisor_requests_received', foreign_keys=[supervisor_id])

    def to_dict(self):
        return {
            'id'           : self.id,
            'scholar_id'   : self.scholar_id,
            'supervisor_id': self.supervisor_id,
            'scholar_name' : f"{self.scholar.first_name} {self.scholar.last_name}".strip() if self.scholar else '',
            'supervisor_name': f"Dr. {self.supervisor.first_name} {self.supervisor.last_name}".strip() if self.supervisor else '',
            'status'       : self.status,
            'created_at'   : self.created_at.isoformat() if self.created_at else None,
        }


# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICATION
# ─────────────────────────────────────────────────────────────────────────────
class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message    = db.Column(db.String(500), nullable=False)
    type       = db.Column(db.String(50), nullable=False)
    # Types: milestone, publication, message, leave_approval, supervisor_request, meeting
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    related_id = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'id'        : self.id,
            'message'   : self.message,
            'type'      : self.type,
            'is_read'   : self.is_read,
            'created_at': _relative_time(self.created_at),
            'related_id': self.related_id,
        }


# ─────────────────────────────────────────────────────────────────────────────
# ACADEMIC MODELS
# ─────────────────────────────────────────────────────────────────────────────
class Milestone(db.Model):
    __tablename__ = 'milestones'
    id          = db.Column(db.Integer, primary_key=True)
    scholar_id  = db.Column(db.Integer, db.ForeignKey('scholars.id'), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date    = db.Column(db.Date)
    status      = db.Column(db.Enum('pending', 'in_progress', 'completed'), default='pending')
    completed_at= db.Column(db.Date, nullable=True)
    faculty_note= db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    scholar = db.relationship('Scholar', backref='milestones')

    def to_dict(self):
        return {
            'id'          : self.id,
            'scholar_id'  : self.scholar_id,
            'title'       : self.title,
            'description' : self.description,
            'due_date'    : str(self.due_date) if self.due_date else None,
            'status'      : self.status,
            'completed_at': str(self.completed_at) if self.completed_at else None,
            'faculty_note': self.faculty_note,
            'created_at'  : str(self.created_at),
        }



class Publication(db.Model):
    __tablename__ = 'publications'
    id          = db.Column(db.Integer, primary_key=True)
    scholar_id  = db.Column(db.Integer, db.ForeignKey('scholars.id'), nullable=False)
    title       = db.Column(db.String(300), nullable=False)
    journal     = db.Column(db.String(200))   # journal/venue name
    venue       = db.Column(db.String(200))   # legacy alias
    pub_type    = db.Column(db.String(50))    # journal, conference, book chapter
    year        = db.Column(db.Integer)
    doi         = db.Column(db.String(200))
    description = db.Column(db.Text)
    visibility  = db.Column(db.String(20), default='faculty')  # public, faculty
    status      = db.Column(db.Enum('under_review', 'approved', 'published', 'rejected'), default='under_review')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    scholar = db.relationship('Scholar', backref='publications')

    def to_dict(self):
        return {
            'id'         : self.id,
            'scholar_id' : self.scholar_id,
            'title'      : self.title,
            'journal'    : self.journal or self.venue,
            'pub_type'   : self.pub_type,
            'year'       : self.year,
            'doi'        : self.doi,
            'description': self.description,
            'visibility' : self.visibility,
            'status'     : self.status,
            'created_at' : self.created_at.isoformat(),
        }


class Stipend(db.Model):
    __tablename__ = 'stipends'
    id         = db.Column(db.Integer, primary_key=True)
    scholar_id = db.Column(db.Integer, db.ForeignKey('scholars.id'), nullable=False)
    month      = db.Column(db.String(20), nullable=False)
    year       = db.Column(db.Integer, nullable=False)
    amount     = db.Column(db.Float, nullable=False)
    fellowship = db.Column(db.String(100))
    status     = db.Column(db.Enum('paid', 'pending', 'on_hold'), default='pending')
    paid_on    = db.Column(db.Date, nullable=True)


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    id              = db.Column(db.Integer, primary_key=True)
    scholar_id      = db.Column(db.Integer, db.ForeignKey('scholars.id'), nullable=False)
    supervisor_id   = db.Column(db.Integer, db.ForeignKey('supervisors.id'), nullable=True)
    leave_type      = db.Column(db.String(100), default='Personal')
    from_date       = db.Column(db.Date, nullable=False)
    to_date         = db.Column(db.Date, nullable=False)
    reason          = db.Column(db.Text)
    submitted_to    = db.Column(db.String(20), default='faculty')  # faculty, admin
    status          = db.Column(db.Enum('pending', 'approved', 'rejected'), default='pending')
    supervisor_note = db.Column(db.Text, nullable=True)
    applied_at      = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at     = db.Column(db.DateTime, nullable=True)

    scholar    = db.relationship('Scholar',    backref='leave_requests')
    supervisor = db.relationship('Supervisor', backref='leave_requests', foreign_keys=[supervisor_id])

    def to_dict(self):
        return {
            'id'             : self.id,
            'scholar_id'     : self.scholar_id,
            'supervisor_id'  : self.supervisor_id,
            'leave_type'     : self.leave_type,
            'from_date'      : str(self.from_date),
            'to_date'        : str(self.to_date),
            'reason'         : self.reason,
            'submitted_to'   : self.submitted_to,
            'status'         : self.status,
            'supervisor_note': self.supervisor_note,
            'applied_at'     : str(self.applied_at),
            'reviewed_at'    : str(self.reviewed_at) if self.reviewed_at else None,
            'scholar_name'   : f"{self.scholar.first_name} {self.scholar.last_name}".strip() if self.scholar else '',
        }


class Message(db.Model):
    __tablename__ = 'messages'
    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    is_read     = db.Column(db.Boolean, default=False)
    sent_at     = db.Column(db.DateTime, default=datetime.utcnow)

    sender   = db.relationship('User', foreign_keys=[sender_id],   backref='messages_sent')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='messages_received')

    def to_dict(self):
        return {
            'id'         : self.id,
            'sender_id'  : self.sender_id,
            'receiver_id': self.receiver_id,
            'content'    : self.content,
            'is_read'    : self.is_read,
            'sent_at'    : str(self.sent_at),
        }


class Meeting(db.Model):
    __tablename__ = 'meetings'
    id            = db.Column(db.Integer, primary_key=True)
    scholar_id    = db.Column(db.Integer, db.ForeignKey('scholars.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisors.id'), nullable=False)
    title         = db.Column(db.String(200))
    scheduled_at  = db.Column(db.DateTime, nullable=False)
    notes         = db.Column(db.Text)
    status        = db.Column(db.Enum('scheduled', 'completed', 'cancelled'), default='scheduled')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    scholar    = db.relationship('Scholar',    backref='meetings', foreign_keys=[scholar_id])
    supervisor = db.relationship('Supervisor', backref='meetings', foreign_keys=[supervisor_id])

    def to_dict(self):
        return {
            'id'           : self.id,
            'scholar_id'   : self.scholar_id,
            'supervisor_id': self.supervisor_id,
            'title'        : self.title,
            'scheduled_at' : str(self.scheduled_at),
            'notes'        : self.notes,
            'status'       : self.status,
            'created_at'   : str(self.created_at),
        }


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT
# ─────────────────────────────────────────────────────────────────────────────
class Document(db.Model):
    __tablename__  = 'documents'
    __table_args__ = {'extend_existing': True}
    id          = db.Column(db.Integer, primary_key=True)
    scholar_id  = db.Column(db.Integer, db.ForeignKey('scholars.id'), nullable=False)
    file_name   = db.Column(db.String(300), nullable=False)
    file_path   = db.Column(db.String(500))
    file_type   = db.Column(db.String(50))
    file_size   = db.Column(db.Integer)
    category    = db.Column(db.String(100), default='Other')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    scholar = db.relationship('Scholar', backref='documents')

    def to_dict(self):
        return {
            'id'         : self.id,
            'scholar_id' : self.scholar_id,
            'file_name'  : self.file_name,
            'file_path'  : self.file_path,
            'file_type'  : self.file_type,
            'file_size'  : self.file_size,
            'category'   : self.category,
            'uploaded_at': str(self.uploaded_at),
        }


# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE
# ─────────────────────────────────────────────────────────────────────────────
class Attendance(db.Model):
    __tablename__  = 'attendance'
    __table_args__ = {'extend_existing': True}
    id         = db.Column(db.Integer, primary_key=True)
    scholar_id = db.Column(db.Integer, db.ForeignKey('scholars.id'), nullable=False)
    date       = db.Column(db.Date, nullable=False)
    status     = db.Column(db.Enum('present', 'absent', 'leave'), default='present')
    marked_by  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    scholar = db.relationship('Scholar', backref='attendance_records')

    def to_dict(self):
        return {
            'id'        : self.id,
            'scholar_id': self.scholar_id,
            'date'      : str(self.date),
            'status'    : self.status,
            'marked_by' : self.marked_by,
        }
