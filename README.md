# ResearchHub — Setup Guide
## Stack: HTML + CSS + JS  |  Python Flask  |  MySQL

---

## FOLDER STRUCTURE

```
ResearchHub/
├── backend/
│   ├── app.py              ← Flask entry point
│   ├── db.py               ← SQLAlchemy instance
│   ├── models.py           ← All MySQL tables
│   ├── requirements.txt    ← Python packages
│   └── routes/
│       ├── auth.py         ← /api/auth/login  /api/auth/register
│       ├── scholar.py      ← /api/scholar/
│       ├── supervisor.py   ← /api/supervisor/
│       ├── milestones.py   ← /api/milestones/
│       ├── documents.py    ← /api/documents/
│       ├── publications.py ← /api/publications/
│       ├── stipend.py      ← /api/stipend/
│       ├── leave.py        ← /api/leave/
│       ├── messages.py     ← /api/messages/
│       └── meetings.py     ← /api/meetings/
│
└── frontend/
    ├── login.html
    ├── register.html
    ├── css/
    │   └── shared.css      ← Common styles for all pages
    ├── js/
    │   └── api.js          ← All API calls in one file
    ├── scholar/
    │   ├── dashboard.html
    │   ├── milestones.html
    │   ├── documents.html
    │   ├── publications.html
    │   ├── stipend.html
    │   ├── leave.html
    │   ├── messages.html
    │   └── profile.html
    └── supervisor/
        ├── dashboard.html
        ├── scholars.html
        ├── approvals.html
        ├── meetings.html
        ├── leave-approvals.html
        └── profile.html
```

---

## STEP 1 — Set Up MySQL Database

Open MySQL Workbench or Command Prompt and run:

```sql
CREATE DATABASE researchhub;
```

That's it. Flask will create all tables automatically on first run.

---

## STEP 2 — Configure Your MySQL Password

Open `backend/app.py` and find this line:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mysql+mysqlconnector://root:YOUR_PASSWORD@localhost/researchhub'
)
```

Replace `YOUR_PASSWORD` with your actual MySQL root password.

---

## STEP 3 — Install Python Packages

Open Command Prompt, go to the backend folder:

```bash
cd ResearchHub/backend
pip install -r requirements.txt
```

This installs:
- flask
- flask-cors
- flask-sqlalchemy
- mysql-connector-python
- werkzeug

---

## STEP 4 — Run the Flask Backend

```bash
cd ResearchHub/backend
python app.py
```

You should see:
```
✅ All tables created successfully.
 * Running on http://127.0.0.1:5000
```

Keep this terminal open while using the app.

---

## STEP 5 — Open the Frontend

Simply open the file in your browser:

```
ResearchHub/frontend/login.html
```

Right-click → Open with → Chrome / Edge / Firefox

OR install the VS Code extension **Live Server** and click "Go Live"

---

## ALL API ENDPOINTS

### Auth
| Method | URL | Description |
|--------|-----|-------------|
| POST | /api/auth/register | Register new scholar |
| POST | /api/auth/login | Login (scholar or supervisor) |

### Scholar
| Method | URL | Description |
|--------|-----|-------------|
| GET | /api/scholar/:id | Get scholar profile |
| PUT | /api/scholar/:id | Update profile |
| GET | /api/scholar/by-supervisor/:id | Get scholars by supervisor |

### Milestones
| Method | URL | Description |
|--------|-----|-------------|
| GET | /api/milestones/:scholar_id | Get all milestones |
| POST | /api/milestones/ | Create milestone |
| PUT | /api/milestones/:id | Update milestone |
| DELETE | /api/milestones/:id | Delete milestone |

### Documents
| Method | URL | Description |
|--------|-----|-------------|
| GET | /api/documents/:scholar_id | Get documents |
| POST | /api/documents/upload | Upload file |
| PUT | /api/documents/:id/status | Approve/reject |
| DELETE | /api/documents/:id | Delete |

### Publications
| Method | URL | Description |
|--------|-----|-------------|
| GET | /api/publications/:scholar_id | Get publications |
| POST | /api/publications/ | Add publication |
| PUT | /api/publications/:id | Update |
| DELETE | /api/publications/:id | Delete |

### Stipend
| Method | URL | Description |
|--------|-----|-------------|
| GET | /api/stipend/:scholar_id | Get stipend records |
| POST | /api/stipend/ | Add record |
| PUT | /api/stipend/:id | Update record |

### Leave
| Method | URL | Description |
|--------|-----|-------------|
| GET | /api/leave/:scholar_id | Get leave requests |
| GET | /api/leave/pending/:supervisor_id | Pending leaves for supervisor |
| POST | /api/leave/ | Apply for leave |
| PUT | /api/leave/:id/review | Approve/reject leave |

### Messages
| Method | URL | Description |
|--------|-----|-------------|
| GET | /api/messages/conversation?user1=&user2= | Get conversation |
| POST | /api/messages/ | Send message |
| GET | /api/messages/unread/:user_id | Unread count |

### Meetings
| Method | URL | Description |
|--------|-----|-------------|
| GET | /api/meetings/scholar/:id | Scholar meetings |
| GET | /api/meetings/supervisor/:id | Supervisor meetings |
| POST | /api/meetings/ | Schedule meeting |
| PUT | /api/meetings/:id | Update meeting |

---

## MySQL Tables Created Automatically

| Table | Purpose |
|-------|---------|
| users | Login credentials + role |
| scholars | Scholar profiles |
| supervisors | Supervisor profiles |
| milestones | Thesis milestones |
| documents | Uploaded documents |
| publications | Research papers |
| stipends | Monthly stipend records |
| leave_requests | Leave applications |
| messages | Scholar-supervisor chat |
| meetings | Review meetings |

---

## TESTING THE API

Use **Thunder Client** in VS Code:

Test login:
```
POST http://localhost:5000/api/auth/login
Body (JSON):
{
  "email": "test@uni.edu",
  "password": "Test@1234",
  "role": "scholar"
}
```

---

## COMMON ERRORS & FIXES

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: flask` | Run `pip install -r requirements.txt` |
| `Access denied for user 'root'` | Wrong MySQL password in app.py |
| `Unknown database 'researchhub'` | Create the database: `CREATE DATABASE researchhub;` |
| CORS error in browser | Flask-CORS is already installed — make sure backend is running |
| `Can't connect to MySQL server` | Start MySQL service in Windows Services |

---

## HOW TO START MYSQL SERVICE (Windows)

1. Press `Win + R` → type `services.msc`
2. Find **MySQL80** (or MySQL)
3. Right-click → **Start**

OR in Command Prompt:
```bash
net start MySQL80
```
"# researchhub" 
