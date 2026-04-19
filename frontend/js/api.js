/* ═══════════════════════════════════════════════════════════════
   ResearchHub v3.6 — Shared API, Auth, Data Model & Mock System
   Single source of truth for the entire portal.
═══════════════════════════════════════════════════════════════ */

const API = 'http://localhost:5000/api';

/* ─── AUTH ─── */
function saveUser(data) { localStorage.setItem('rh_user', JSON.stringify(data)); }
function getUser()      { return JSON.parse(localStorage.getItem('rh_user') || 'null'); }
function logout()       { localStorage.removeItem('rh_user'); window.location.href = 'login.html'; }

function requireAuth(role) {
    const u = getUser();
    if (!u) { window.location.href = 'login.html'; return null; }
    if (role) {
        const allowed = Array.isArray(role) ? role : [role];
        const isFaculty = u.role === 'faculty' || u.role === 'supervisor';
        const ok = allowed.some(r => (r === 'faculty' || r === 'supervisor') ? isFaculty : r === u.role);
        if (!ok) { window.location.href = 'login.html'; return null; }
    }
    return u;
}

/* ════════════════════════════════════════════════
   MOCK DATA FALLBACKS (Used when backend is offline)
════════════════════════════════════════════════ */
const MOCK_SCHOLARS = [
    { id:1, user_id:101, name:'Lekisha Raj', role:'scholar', department:'Mathematics', thesis_stage:'Coursework', progress_pct:35, enrollment_id:'SCH2021001', supervisor_id:1 },
    { id:2, user_id:102, name:'Jahnavi Priya', role:'scholar', department:'CSE', thesis_stage:'Research', progress_pct:50, enrollment_id:'SCH2021002', supervisor_id:1 },
    { id:3, user_id:103, name:'Prem Kumar', role:'scholar', department:'CSE', thesis_stage:'Coursework', progress_pct:40, enrollment_id:'SCH2021003', supervisor_id:1 }
];

const MOCK_FACULTY = [
    { id:1, user_id:1, name:'Dr. Dany Thomas', role:'faculty', department:'Mathematics', student_ids:[101,102,103] }
];

/* ─── HTTP HELPERS ─── */
async function _fetchWithFallback(path, opts, method, body) {
    try {
        const r = await fetch(`${API}${path}`, { ...opts, signal: AbortSignal.timeout(3500) });
        const d = await r.json(); 
        if (!r.ok) throw d; 
        return d;
    } catch (e) {
        console.warn(`Backend fail for ${path}. Checking fallback...`);
        // Simple logic for basic pages when backend is down
        if (path.includes('/scholars')) return MOCK_SCHOLARS;
        if (path.includes('/conversations-list')) return [];
        if (path.includes('/attendance')) return { records: [], summary: {present:0,absent:0,leave:0,total:0}, pct:0 };
        throw e;
    }
}

const apiGet    = p         => _fetchWithFallback(p, {}, 'GET');
const apiPost   = (p, b)    => _fetchWithFallback(p, { method:'POST',  headers:{'Content-Type':'application/json'}, body:JSON.stringify(b) }, 'POST', b);
const apiPut    = (p, b={}) => _fetchWithFallback(p, { method:'PUT',   headers:{'Content-Type':'application/json'}, body:JSON.stringify(b) }, 'PUT', b);
const apiDelete = p         => _fetchWithFallback(p, { method:'DELETE' }, 'DELETE');

/* ─── UI UTILITIES ─── */
function toast(msg, type='success') {
    const el = document.createElement('div');
    el.className = `toast toast-${type}`; el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(()=>el.remove(), 3200);
}
function badgeClass(status='') {
    const s=(status||'').toLowerCase().replace(/[\s_]/g,'-');
    if (['completed','approved','published','active','present'].includes(s)) return 'completed';
    if (['rejected','failed','suspended','absent'].includes(s)) return 'rejected';
    return 'pending';
}
function formatDate(d) {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'});
}
function initials(name) {
    if (!name) return '?';
    return name.split(' ').map(n=>n[0]).join('').substring(0,2).toUpperCase();
}
