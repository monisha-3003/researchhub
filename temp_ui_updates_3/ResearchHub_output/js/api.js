/* ═══════════════════════════════════════════════
   ResearchHub — Shared API & Auth helpers
   All pages import this file.
═══════════════════════════════════════════════ */
const API = 'http://localhost:5000/api';

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

/* ── HTTP helpers ── */
async function apiGet(path) {
    const r = await fetch(`${API}${path}`);
    if (!r.ok) throw await r.json();
    return r.json();
}

async function apiPost(path, body) {
    const r = await fetch(`${API}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const data = await r.json();
    if (!r.ok) throw data;
    return data;
}

async function apiPut(path, body = {}) {
    const r = await fetch(`${API}${path}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const data = await r.json();
    if (!r.ok) throw data;
    return data;
}

async function apiDelete(path) {
    const r = await fetch(`${API}${path}`, {
        method: 'DELETE'
    });
    const data = await r.json();
    if (!r.ok) throw data;
    return data;
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
    const s = status.toLowerCase().replace(' ', '-');
    if (s === 'completed' || s === 'approved' || s === 'published') return 'completed';
    if (s === 'in-progress') return 'in-progress';
    if (s === 'pending') return 'pending';
    return 'pending';
}
