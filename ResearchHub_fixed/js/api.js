/* ═══════════════════════════════════════════════
   ResearchHub — Shared API & Auth helpers
   All pages import this file.
═══════════════════════════════════════════════ */
const API = 'http://researchhub-production-637b.up.railway.app';

/* ── Auth helpers ── */
function saveUser(data) { localStorage.setItem('rh_user', JSON.stringify(data)); }
function getUser()      { return JSON.parse(localStorage.getItem('rh_user') || 'null'); }
function logout()       { localStorage.removeItem('rh_user'); window.location.href = 'login.html'; }

function requireAuth(role) {
    const u = getUser();
    if (!u) { window.location.href = 'login.html'; return null; }
    if (role) {
        const allowed = Array.isArray(role) ? role : [role];
        // Normalize: treat 'faculty' and 'supervisor' as the same role
        const isFaculty = u.role === 'faculty' || u.role === 'supervisor';
        const isAllowed = allowed.some(r => {
            if (r === 'faculty' || r === 'supervisor') return isFaculty;
            return r === u.role;
        });
        if (!isAllowed) { window.location.href = 'login.html'; return null; }
    }
    return u;
}

/* ═══════════════════════════════════════════════
   MOCK DATA SYSTEM — used when backend is offline
═══════════════════════════════════════════════ */

const MOCK_SCHOLARS = [
    { id: 1, user_id: 101, name: 'Lekisha Raj',   department: 'Mathematics',                  research_focus: 'Coursework',        thesis_stage: 'Coursework',        progress_pct: 35, enrollment_id: 'SCH2021001', email: 'lekisha@univ.edu',   phone: '9876543210', gender: 'Female', role: 'scholar' },
    { id: 2, user_id: 102, name: 'Jahnavi Priya', department: 'Computer Science & Engineering', research_focus: 'Research Proposal', thesis_stage: 'Research Proposal', progress_pct: 50, enrollment_id: 'SCH2021002', email: 'jahnavi@univ.edu',  phone: '9876543211', gender: 'Female', role: 'scholar' },
    { id: 3, user_id: 103, name: 'Prem Kumar',    department: 'Computer Science & Engineering', research_focus: 'Coursework',        thesis_stage: 'Coursework',        progress_pct: 40, enrollment_id: 'SCH2021003', email: 'prem@univ.edu',    phone: '9876543212', gender: 'Male',   role: 'scholar' },
];

const MOCK_MESSAGES_STORE_KEY = 'rh_mock_messages';
const MOCK_LEAVE_STORE_KEY    = 'rh_mock_leaves';
const MOCK_ATTENDANCE_KEY     = 'rh_mock_attendance';

function getMockMessages() {
    return JSON.parse(localStorage.getItem(MOCK_MESSAGES_STORE_KEY) || '[]');
}
function saveMockMessages(msgs) {
    localStorage.setItem(MOCK_MESSAGES_STORE_KEY, JSON.stringify(msgs));
}

function getMockLeaves() {
    const stored = localStorage.getItem(MOCK_LEAVE_STORE_KEY);
    if (stored) return JSON.parse(stored);
    // Seed default leaves
    const defaults = [
        { id: 1, scholar_id: 101, scholar_name: 'Lekisha Raj',   leave_type: 'Medical',   from_date: '2025-04-01', to_date: '2025-04-03', reason: 'Medical appointment and recovery.', status: 'pending',  created_at: '2025-03-28' },
        { id: 2, scholar_id: 102, scholar_name: 'Jahnavi Priya', leave_type: 'Personal',  from_date: '2025-03-10', to_date: '2025-03-12', reason: 'Family function attendance.',       status: 'approved', created_at: '2025-03-05', reviewed_at: '2025-03-06' },
        { id: 3, scholar_id: 103, scholar_name: 'Prem Kumar',    leave_type: 'Academic',  from_date: '2025-02-20', to_date: '2025-02-21', reason: 'Conference presentation.',          status: 'rejected', created_at: '2025-02-15', reviewed_at: '2025-02-16' },
    ];
    localStorage.setItem(MOCK_LEAVE_STORE_KEY, JSON.stringify(defaults));
    return defaults;
}
function saveMockLeaves(leaves) {
    localStorage.setItem(MOCK_LEAVE_STORE_KEY, JSON.stringify(leaves));
}

function getMockAttendance() {
    const stored = localStorage.getItem(MOCK_ATTENDANCE_KEY);
    if (stored) return JSON.parse(stored);
    // Generate realistic attendance for 3 months back
    const records = {};
    const today = new Date();
    MOCK_SCHOLARS.forEach(s => {
        records[s.user_id] = [];
        // Get approved leaves for this scholar
        const leaves = getMockLeaves().filter(l => l.scholar_id === s.user_id && l.status === 'approved');
        const leaveDates = new Set();
        leaves.forEach(l => {
            const start = new Date(l.from_date), end = new Date(l.to_date);
            for (let d = new Date(start); d <= end; d.setDate(d.getDate()+1)) {
                leaveDates.add(d.toISOString().split('T')[0]);
            }
        });

        for (let m = 2; m >= 0; m--) {
            const ref = new Date(today.getFullYear(), today.getMonth() - m, 1);
            const daysInMonth = new Date(ref.getFullYear(), ref.getMonth()+1, 0).getDate();
            for (let d = 1; d <= daysInMonth; d++) {
                const dt = new Date(ref.getFullYear(), ref.getMonth(), d);
                if (dt > today) continue;
                const weekday = dt.getDay();
                if (weekday === 0 || weekday === 6) continue; // skip weekends
                const dateStr = dt.toISOString().split('T')[0];
                let status;
                if (leaveDates.has(dateStr)) {
                    status = 'leave';
                } else {
                    // ~80% present, ~20% absent
                    status = Math.random() < 0.8 ? 'present' : 'absent';
                }
                records[s.user_id].push({ date: dateStr, status, scholar_id: s.user_id });
            }
        }
    });
    localStorage.setItem(MOCK_ATTENDANCE_KEY, JSON.stringify(records));
    return records;
}
function saveMockAttendance(att) {
    localStorage.setItem(MOCK_ATTENDANCE_KEY, JSON.stringify(att));
}

/* Resolve mock API calls */
function resolveMockApi(path, method = 'GET', body = null) {
    const user = getUser();
    const uid  = user ? user.id : null;

    // GET /faculty/scholars/:id  OR  /supervisor/:id/scholars
    if (method === 'GET' && (path.match(/^\/faculty\/scholars\/\d+$/) || path.match(/^\/supervisor\/\d+\/scholars$/))) {
        return { ok: true, data: MOCK_SCHOLARS };
    }

    // GET /profile/:id
    if (method === 'GET' && path.match(/^\/profile\/(\d+)$/)) {
        const id = parseInt(path.split('/')[2]);
        const s = MOCK_SCHOLARS.find(s => s.user_id === id);
        if (s) return { ok: true, data: s };
        // faculty profile
        if (id === uid) return { ok: true, data: { ...user, role: 'faculty', department: user.profile?.department || 'Computer Science' } };
        return { ok: false, data: { detail: 'Not found' } };
    }

    // GET /messages/conversations-list/:uid
    if (method === 'GET' && path.match(/^\/messages\/conversations-list\/\d+$/)) {
        const msgs = getMockMessages();
        const myId = parseInt(path.split('/').pop());
        // Build conversation list
        const partnerMap = {};
        msgs.forEach(m => {
            const partnerId = m.sender_id === myId ? m.receiver_id : m.receiver_id === myId ? m.sender_id : null;
            if (!partnerId) return;
            if (!partnerMap[partnerId] || new Date(m.sent_at) > new Date(partnerMap[partnerId].sent_at)) {
                partnerMap[partnerId] = m;
            }
        });
        const conversations = Object.entries(partnerMap).map(([pid, lastMsg]) => {
            const partner = MOCK_SCHOLARS.find(s => s.user_id == pid) || { name: user.name, role: 'faculty', user_id: pid };
            return {
                user_id: parseInt(pid),
                name: partner.name,
                role: partner.role || 'scholar',
                last_message: lastMsg.content,
                unread: 0,
            };
        });
        // Always include all scholars in faculty's conversation list
        if (user && (user.role === 'faculty' || user.role === 'supervisor')) {
            MOCK_SCHOLARS.forEach(s => {
                if (!partnerMap[s.user_id]) {
                    conversations.push({ user_id: s.user_id, name: s.name, role: 'scholar', last_message: null, unread: 0 });
                }
            });
        }
        return { ok: true, data: conversations };
    }

    // GET /messages/conversation?user1=&user2=
    if (method === 'GET' && path.startsWith('/messages/conversation')) {
        const params = new URLSearchParams(path.split('?')[1]);
        const u1 = parseInt(params.get('user1')), u2 = parseInt(params.get('user2'));
        const msgs = getMockMessages().filter(m =>
            (m.sender_id === u1 && m.receiver_id === u2) ||
            (m.sender_id === u2 && m.receiver_id === u1)
        ).sort((a,b) => new Date(a.sent_at) - new Date(b.sent_at));
        return { ok: true, data: msgs };
    }

    // POST /messages/
    if (method === 'POST' && path === '/messages/') {
        const msgs = getMockMessages();
        const newMsg = { id: Date.now(), ...body, sent_at: new Date().toISOString(), is_read: false };
        msgs.push(newMsg);
        saveMockMessages(msgs);
        return { ok: true, data: newMsg };
    }

    // GET /messages/available-recipients/:uid
    if (method === 'GET' && path.match(/^\/messages\/available-recipients\/\d+$/)) {
        return { ok: true, data: MOCK_SCHOLARS };
    }

    // GET /supervisor/:id/leave-requests
    if (method === 'GET' && path.match(/^\/supervisor\/\d+\/leave-requests/)) {
        let leaves = getMockLeaves();
        if (path.includes('status=pending')) leaves = leaves.filter(l => l.status === 'pending');
        return { ok: true, data: leaves };
    }

    // PUT /supervisor/leave/:id/review
    if (method === 'PUT' && path.match(/^\/supervisor\/leave\/\d+\/review$/)) {
        const id = parseInt(path.split('/')[3]);
        const leaves = getMockLeaves();
        const idx = leaves.findIndex(l => l.id === id);
        if (idx !== -1) {
            leaves[idx].status = body.status;
            leaves[idx].reviewed_at = new Date().toISOString();
            saveMockLeaves(leaves);
            // Sync: if approved, mark attendance as 'leave' for date range
            if (body.status === 'approved') {
                const l = leaves[idx];
                const att = getMockAttendance();
                const scholarAtt = att[l.scholar_id] || [];
                const start = new Date(l.from_date), end = new Date(l.to_date);
                for (let d = new Date(start); d <= end; d.setDate(d.getDate()+1)) {
                    const ds = d.toISOString().split('T')[0];
                    const existing = scholarAtt.find(r => r.date === ds);
                    if (existing) existing.status = 'leave';
                    else scholarAtt.push({ date: ds, status: 'leave', scholar_id: l.scholar_id });
                }
                att[l.scholar_id] = scholarAtt;
                saveMockAttendance(att);
            }
        }
        return { ok: true, data: { message: 'Updated' } };
    }

    // GET /attendance/:scholarId
    if (method === 'GET' && path.match(/^\/attendance\/\d+/)) {
        const scholarId = parseInt(path.split('/')[2]);
        const params = new URLSearchParams(path.includes('?') ? path.split('?')[1] : '');
        const month = parseInt(params.get('month')) || new Date().getMonth()+1;
        const year  = parseInt(params.get('year'))  || new Date().getFullYear();

        // Find scholar by user_id or id
        const scholar = MOCK_SCHOLARS.find(s => s.id === scholarId || s.user_id === scholarId);
        const key = scholar ? scholar.user_id : scholarId;
        const att = getMockAttendance();
        const allRecords = att[key] || [];

        const records = allRecords.filter(r => {
            const d = new Date(r.date);
            return d.getMonth()+1 === month && d.getFullYear() === year;
        });

        const summary = { present: 0, absent: 0, leave: 0, total: records.length };
        records.forEach(r => { if (summary[r.status] !== undefined) summary[r.status]++; });
        const pct = summary.total > 0 ? Math.round((summary.present / summary.total) * 100) : 0;

        return { ok: true, data: { records, summary, pct } };
    }

    // POST /attendance/
    if (method === 'POST' && path === '/attendance/') {
        const att = getMockAttendance();
        const sid = body.scholar_id;
        const scholar = MOCK_SCHOLARS.find(s => s.id === sid || s.user_id === sid);
        const key = scholar ? scholar.user_id : sid;
        if (!att[key]) att[key] = [];
        const existing = att[key].find(r => r.date === body.date);
        if (existing) existing.status = body.status;
        else att[key].push({ date: body.date, status: body.status, scholar_id: key });
        saveMockAttendance(att);
        return { ok: true, data: { message: 'Marked' } };
    }

    // GET /supervisor/:id/publications
    if (method === 'GET' && path.match(/^\/supervisor\/\d+\/publications/)) {
        return { ok: true, data: [] };
    }

    // GET /supervisor/:id/supervisor-requests
    if (method === 'GET' && path.match(/^\/supervisor\/\d+\/supervisor-requests/)) {
        return { ok: true, data: [] };
    }

    // GET /notifications/:uid
    if (method === 'GET' && path.match(/^\/notifications\/\d+$/)) {
        return { ok: true, data: { unread_count: 0, notifications: [] } };
    }

    // PUT /notifications/...
    if (method === 'PUT' && path.startsWith('/notifications/')) {
        return { ok: true, data: {} };
    }

    return null; // Not handled by mock
}

/* ── HTTP helpers with mock fallback ── */
async function apiGet(path) {
    try {
        const r = await fetch(`${API}${path}`);
        if (!r.ok) throw await r.json();
        return r.json();
    } catch(err) {
        const mock = resolveMockApi(path, 'GET');
        if (mock) {
            if (!mock.ok) throw mock.data;
            return mock.data;
        }
        throw err;
    }
}

async function apiPost(path, body) {
    try {
        const r = await fetch(`${API}${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await r.json();
        if (!r.ok) throw data;
        return data;
    } catch(err) {
        const mock = resolveMockApi(path, 'POST', body);
        if (mock) {
            if (!mock.ok) throw mock.data;
            return mock.data;
        }
        throw err;
    }
}

async function apiPut(path, body = {}) {
    try {
        const r = await fetch(`${API}${path}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await r.json();
        if (!r.ok) throw data;
        return data;
    } catch(err) {
        const mock = resolveMockApi(path, 'PUT', body);
        if (mock) {
            if (!mock.ok) throw mock.data;
            return mock.data;
        }
        throw err;
    }
}

async function apiDelete(path) {
    try {
        const r = await fetch(`${API}${path}`, { method: 'DELETE' });
        const data = await r.json();
        if (!r.ok) throw data;
        return data;
    } catch(err) {
        const mock = resolveMockApi(path, 'DELETE');
        if (mock) {
            if (!mock.ok) throw mock.data;
            return mock.data;
        }
        throw err;
    }
}

/* ── Toast notifications ── */
function toast(msg, type = 'success') {
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3000);
}

/* ── Badge status colors ── */
function badgeClass(status = '') {
    const s = (status || '').toLowerCase().replace(' ', '-');
    if (['completed','approved','published','active','accepted'].includes(s)) return 'badge-success';
    if (['rejected','failed','suspended','absent','debarred'].includes(s))    return 'badge-danger';
    if (['pending','under_review','in_progress','in-progress'].includes(s))   return 'badge-warning';
    return 'badge-info';
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-IN', {
        day: 'numeric', month: 'short', year: 'numeric'
    });
}

