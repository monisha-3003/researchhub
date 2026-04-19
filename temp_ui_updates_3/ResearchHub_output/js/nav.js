/* ═══════════════════════════════════════════════
   ResearchHub — Shared Sidebar / Nav renderer
   + Notification MODAL System (Center Popup)
   + Badge Helpers
═══════════════════════════════════════════════ */

const SCHOLAR_NAV = [
    { href: 'scholar-dashboard.html', icon: 'fa-chart-line',         label: 'Dashboard' },
    { href: 'my-professor.html',      icon: 'fa-chalkboard-teacher', label: 'My Professor' },
    { href: 'directory.html',         icon: 'fa-address-book',       label: 'Faculty Directory' },
    { href: 'milestones.html',        icon: 'fa-tasks',              label: 'Milestones' },
    { href: 'publications.html',      icon: 'fa-book',               label: 'Publications' },
    { href: 'leaverequest.html',      icon: 'fa-calendar-alt',       label: 'Leave Request' },
    { href: 'attendance.html',        icon: 'fa-calendar-check',     label: 'Attendance' },
    { href: 'documents.html',         icon: 'fa-folder-open',        label: 'Documents' },
    { href: 'stipend.html',           icon: 'fa-rupee-sign',         label: 'Stipend' },
    { href: 'messages.html',          icon: 'fa-envelope',           label: 'Messages', badge: 'msg' },
    { href: 'profile.html',           icon: 'fa-user-circle',        label: 'Profile' },
];

const FACULTY_NAV = [
    { href: 'supervisor-dashboard.html', icon: 'fa-chart-line',      label: 'Dashboard' },
    { href: 'messages.html',             icon: 'fa-envelope',        label: 'Messages', badge: 'msg' },
    { href: 'sup-profile.html',          icon: 'fa-user-tie',        label: 'My Profile' },
    { href: 'sup-scholars.html',         icon: 'fa-users',           label: 'My Scholars' },
    { href: 'sup-attendance.html',       icon: 'fa-calendar-check',  label: 'Attendance' },
    { href: 'sup-leave.html',            icon: 'fa-clipboard-check', label: 'Leave Approvals', badge: 'leave' },
    { href: 'sup-milestones.html',       icon: 'fa-tasks',           label: 'Milestones' },
    { href: 'sup-publications.html',     icon: 'fa-book-open',       label: 'Publications' },
];

const ADMIN_NAV = [
    { href: 'admin-dashboard.html', icon: 'fa-grid-2',              label: 'Overview' },
    { href: 'admin-dashboard.html', icon: 'fa-user-graduate',       label: 'Scholars' },
    { href: 'admin-dashboard.html', icon: 'fa-chalkboard-teacher',  label: 'Faculty' },
    { href: 'admin-dashboard.html', icon: 'fa-calendar-check',      label: 'Leaves' },
    { href: 'messages.html',        icon: 'fa-envelope',            label: 'Messages' },
];

/* ─────────────────────────────────────────────────────────
   NOTIFICATION MODAL — injected once into <body>
───────────────────────────────────────────────────────── */
function injectNotificationModal() {
    if (document.getElementById('notificationModal')) return;

    const modal = document.createElement('div');
    modal.id = 'notificationModal';
    modal.className = 'notification-modal';
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-label', 'Notifications');

    modal.innerHTML = `
        <div class="notif-modal-content" id="notifModalContent">
            <div class="notif-modal-header">
                <div class="notif-modal-title">
                    <span class="notif-modal-icon-wrap"><i class="fas fa-bell"></i></span>
                    <h2>Notifications</h2>
                    <span class="notif-modal-count" id="notifModalCount" style="display:none">0</span>
                </div>
                <div class="notif-modal-actions">
                    <button class="notif-mark-all-btn" onclick="markAllRead()" title="Mark all as read">
                        <i class="fas fa-check-double"></i> Mark all read
                    </button>
                    <button class="notif-close-btn" id="notifModalClose" aria-label="Close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="notif-modal-body" id="notifModalBody">
                <div class="notif-modal-loading">
                    <div class="notif-spinner"></div>
                    <p>Loading notifications…</p>
                </div>
            </div>
            <div class="notif-modal-footer">
                <span id="notifModalFooterText" class="notif-footer-text">Checking for updates…</span>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    modal.addEventListener('click', (e) => { if (e.target === modal) closeNotifModal(); });
    document.getElementById('notifModalClose').addEventListener('click', closeNotifModal);
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeNotifModal(); });
}

function openNotifModal() {
    const modal = document.getElementById('notificationModal');
    if (!modal) return;
    modal.style.display = 'flex';
    modal.offsetHeight; // force reflow for animation
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
    const user = getUser();
    if (user) loadNotifications(user.id);
}

function closeNotifModal() {
    const modal = document.getElementById('notificationModal');
    if (!modal) return;
    modal.classList.remove('open');
    modal.classList.add('closing');
    setTimeout(() => {
        modal.style.display = 'none';
        modal.classList.remove('closing');
        document.body.style.overflow = '';
    }, 280);
}

/* ─────────────────────────────────────────────────────────
   renderSidebar
───────────────────────────────────────────────────────── */
function renderSidebar(activeHref) {
    const user = getUser();
    if (!user) return;

    document.body.className = `portal-${user.role}`;

    const isAdmin   = user.role === 'admin';
    const isFaculty = user.role === 'faculty' || user.role === 'supervisor';

    let navItems = SCHOLAR_NAV;
    let portal   = 'Scholar Portal';
    if (isAdmin)        { navItems = ADMIN_NAV;   portal = 'Admin Portal'; }
    else if (isFaculty) { navItems = FACULTY_NAV; portal = 'Faculty Portal'; }

    const name     = user.name || 'User';
    const initials = name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'U';
    const dept     = (user.profile && user.profile.department) ? user.profile.department : 'Academic Dept';

    const navHTML = navItems.map(item => {
        const active    = activeHref && item.href === activeHref ? 'active' : '';
        const badgeHTML = item.badge
            ? `<span class="nav-badge" id="badge-${item.badge}" style="display:none">0</span>`
            : '';
        return `
        <a href="${item.href}" class="nav-link ${active}">
            <i class="fas ${item.icon}"></i>
            <span>${item.label}</span>
            ${badgeHTML}
        </a>`;
    }).join('');

    const html = `
    <aside class="sidebar">
        <div class="sidebar-brand">
            <div class="brand-icon"><i class="fas fa-layer-group"></i></div>
            <div>
                <div class="brand-name">ResearchHub <span style="color:#4ade80;font-size:0.7rem;font-weight:700">v3.5</span></div>
                <div class="brand-sub">${portal}</div>
            </div>
        </div>

        <nav class="sidebar-nav nav-links">${navHTML}</nav>

        <div class="sidebar-footer">
            <div class="notif-bell-wrap" id="notifBellWrap">
                <button class="notif-bell sidebar-bell" id="notifBell"
                        onclick="openNotifModal()"
                        title="View Notifications"
                        aria-haspopup="dialog">
                    <i class="fas fa-bell"></i>
                    <span>Notifications</span>
                    <span class="notif-badge" id="notifBadge" style="display:none">0</span>
                </button>
            </div>

            <div class="user-info">
                <div class="u-avatar">${initials}</div>
                <div class="u-details">
                    <div class="u-name">${name}</div>
                    <div class="u-role">${dept}</div>
                </div>
            </div>
            <button class="logout-btn" onclick="logout()">
                <i class="fas fa-sign-out-alt"></i>
                <span>Sign Out</span>
            </button>
        </div>
    </aside>`;

    const container = document.getElementById('sidebar-container');
    if (container) container.innerHTML = html;

    renderTopBell();
    injectNotificationModal();
    initNotifications();
    loadPendingBadge();
}

/* ─────────────────────────────────────────────────────────
   renderTopBell — top-bar circular bell button
───────────────────────────────────────────────────────── */
function renderTopBell() {
    const container = document.getElementById('top-notif-container');
    if (!container) return;

    container.innerHTML = `
        <button class="top-bell-btn" id="notifBellTop"
                onclick="openNotifModal()"
                title="View Notifications"
                aria-haspopup="dialog">
            <i class="fas fa-bell"></i>
            <span class="notif-badge" id="notifBadgeTop" style="display:none">0</span>
        </button>
    `;
}

/* ─────────────────────────────────────────────────────────
   NOTIFICATION DATA & RENDERING
───────────────────────────────────────────────────────── */
let _notifInterval = null;

function initNotifications() {
    const user = getUser();
    if (!user) return;
    loadNotifications(user.id);
    if (_notifInterval) clearInterval(_notifInterval);
    _notifInterval = setInterval(() => loadNotifications(user.id), 30000);
}

async function loadNotifications(userId) {
    try {
        const data = await apiGet(`/notifications/${userId}`);
        updateNotifBadge(data.unread_count);
        renderNotifModalBody(data.notifications);
    } catch (err) { /* silently fail */ }
}

function updateNotifBadge(count) {
    ['notifBadge', 'notifBadgeTop'].forEach(id => {
        const b = document.getElementById(id);
        if (!b) return;
        if (count > 0) { b.style.display = 'flex'; b.textContent = count > 99 ? '99+' : count; }
        else           { b.style.display = 'none'; }
    });

    const chip = document.getElementById('notifModalCount');
    if (chip) {
        if (count > 0) { chip.style.display = 'inline-flex'; chip.textContent = count > 99 ? '99+' : count; }
        else           { chip.style.display = 'none'; }
    }

    const footer = document.getElementById('notifModalFooterText');
    if (footer) {
        footer.textContent = count > 0
            ? `${count} unread notification${count > 1 ? 's' : ''}`
            : 'All caught up — no unread notifications';
    }
}

const NOTIF_META = {
    leave_approval    : { emoji: '📋', color: '#fbbf24', bg: 'rgba(251,191,36,0.12)'  },
    publication       : { emoji: '📄', color: '#60a5fa', bg: 'rgba(96,165,250,0.12)'  },
    meeting           : { emoji: '📅', color: '#34d399', bg: 'rgba(52,211,153,0.12)'  },
    supervisor_request: { emoji: '🎓', color: '#a78bfa', bg: 'rgba(167,139,250,0.14)' },
    message           : { emoji: '💬', color: '#00D4FF', bg: 'rgba(0,212,255,0.10)'   },
    milestone         : { emoji: '🏁', color: '#f87171', bg: 'rgba(248,113,113,0.12)' },
};

function renderNotifModalBody(notifications) {
    const body = document.getElementById('notifModalBody');
    if (!body) return;

    if (!notifications || notifications.length === 0) {
        body.innerHTML = `
            <div class="notif-modal-empty">
                <div class="notif-empty-icon">🔔</div>
                <p>No notifications yet</p>
                <span>You're all caught up!</span>
            </div>`;
        return;
    }

    const unread = notifications.filter(n => !n.is_read);
    const read   = notifications.filter(n =>  n.is_read);
    let html = '';

    if (unread.length) {
        html += `<div class="notif-group-label">New <span class="notif-group-count">${unread.length}</span></div>`;
        html += unread.map(renderNotifItem).join('');
    }
    if (read.length) {
        html += `<div class="notif-group-label earlier-label">Earlier</div>`;
        html += read.map(renderNotifItem).join('');
    }

    body.innerHTML = html;
}

function renderNotifItem(n) {
    const meta = NOTIF_META[n.type] || { emoji: '🔔', color: '#8B5CF6', bg: 'rgba(139,92,246,0.12)' };
    const time = n.created_at ? formatRelativeTime(n.created_at) : '';
    return `
    <div class="notif-modal-item ${n.is_read ? '' : 'unread'}"
         onclick="handleNotifClick(${n.id}, '${n.type}', ${n.related_id || 'null'})">
        <div class="notif-item-icon" style="background:${meta.bg};color:${meta.color}">${meta.emoji}</div>
        <div class="notif-item-body">
            <p class="notif-item-msg">${n.message}</p>
            <span class="notif-item-time"><i class="fas fa-clock"></i> ${time}</span>
        </div>
        ${!n.is_read ? `<span class="notif-unread-dot"></span>` : ''}
    </div>`;
}

function formatRelativeTime(dateStr) {
    try {
        const diff = Date.now() - new Date(dateStr).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1)  return 'Just now';
        if (mins < 60) return `${mins}m ago`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24)  return `${hrs}h ago`;
        const days = Math.floor(hrs / 24);
        if (days < 7)  return `${days}d ago`;
        return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
    } catch { return dateStr; }
}

async function handleNotifClick(notifId, type, relatedId) {
    try { await apiPut(`/notifications/${notifId}/read`); } catch(_) {}
    closeNotifModal();
    const routes = {
        leave_approval    : 'leaverequest.html',
        publication       : 'publications.html',
        meeting           : 'sup-meetings.html',
        supervisor_request: 'my-professor.html',
        message           : 'messages.html',
        milestone         : 'milestones.html',
    };
    if (routes[type]) window.location.href = routes[type];
}

async function markAllRead() {
    const user = getUser();
    if (!user) return;
    try {
        await apiPut(`/notifications/read-all/${user.id}`);
        document.querySelectorAll('.notif-modal-item.unread').forEach(el => {
            el.classList.remove('unread');
            const dot = el.querySelector('.notif-unread-dot');
            if (dot) dot.remove();
        });
        const newLabel = document.querySelector('.notif-group-label:not(.earlier-label)');
        if (newLabel) newLabel.remove();
        updateNotifBadge(0);
    } catch(_) {}
}

async function loadPendingBadge() {
    const user = getUser();
    if (!user) return;
    try {
        if (user.role === 'supervisor' || user.role === 'faculty') {
            const sv_id = user.supervisor_id;
            if (sv_id) {
                const leaves = await apiGet(`/supervisor/${sv_id}/leave-requests`);
                const el = document.getElementById('badge-leave');
                if (el && leaves.length > 0) {
                    el.textContent   = leaves.length;
                    el.style.display = 'inline-block';
                }
            }
        }
    } catch(_) {}
}

/* ─────────────────────────────────────────────────────────
   GLOBAL HELPERS
───────────────────────────────────────────────────────── */
function badgeClass(status) {
    if (!status) return 'badge-default';
    const s = status.toLowerCase();
    if (['approved', 'accepted', 'completed', 'active', 'published'].includes(s)) return 'badge-success';
    if (['rejected', 'failed', 'suspended', 'absent', 'debarred'].includes(s))    return 'badge-danger';
    if (['pending', 'under_review', 'in_progress'].includes(s))                   return 'badge-warning';
    return 'badge-info';
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}
