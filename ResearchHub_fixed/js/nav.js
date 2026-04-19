/* ═══════════════════════════════════════════════
   ResearchHub — Shared Sidebar / Nav renderer
   + Notification Bell System
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
    { href: 'admin-dashboard.html', icon: 'fa-grid-2', label: 'Overview' },
    { href: 'admin-dashboard.html', icon: 'fa-user-graduate', label: 'Scholars' },
    { href: 'admin-dashboard.html', icon: 'fa-chalkboard-teacher', label: 'Faculty' },
    { href: 'admin-dashboard.html', icon: 'fa-calendar-check', label: 'Leaves' },
    { href: 'messages.html',        icon: 'fa-envelope', label: 'Messages' },
];

// ─────────────────────────────────────────────────────────
// renderSidebar — builds and injects the sidebar HTML
// ─────────────────────────────────────────────────────────
function renderSidebar(activeHref) {
    const user = getUser();
    if (!user) return;

    // Apply role-based theme to body
    document.body.className = `portal-${user.role}`;

    const isAdmin = user.role === 'admin';
    const isFaculty = user.role === 'faculty' || user.role === 'supervisor';

    let navItems = SCHOLAR_NAV;
    let portal = 'Scholar Portal';

    if (isAdmin) {
        navItems = ADMIN_NAV;
        portal = 'Admin Portal';
    } else if (isFaculty) {
        navItems = FACULTY_NAV;
        portal = 'Faculty Portal';
    }

    const name     = user.name || 'User';
    const initials = name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'U';
    const dept     = (user.profile && user.profile.department) ? user.profile.department : 'Academic Dept';

    const navHTML = navItems.map(item => {
        const active = activeHref && item.href === activeHref ? 'active' : '';
        const badgeHTML = item.badge ? `<span class="nav-badge" id="badge-${item.badge}" style="display:none">0</span>` : '';
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
            <!-- Notification Bell — single unified button -->
            <div class="notif-bell-wrap" id="notifBellWrap">
                <button class="notif-bell" id="notifBell" onclick="toggleNotifDropdown(event)" title="Notifications">
                    <i class="fas fa-bell" style="color:var(--primary);font-size:1rem;flex-shrink:0"></i>
                    <span style="font-size:0.875rem;font-weight:500;color:rgba(255,255,255,0.75);flex:1">Notifications</span>
                    <span class="notif-badge" id="notifBadge" style="display:none">0</span>
                </button>
                <div class="notif-dropdown" id="notifDropdown">
                    <div class="notif-header">
                        <span>Notifications</span>
                        <button onclick="markAllRead()" style="font-size:0.75rem;color:var(--primary);background:none;border:none;cursor:pointer;">Mark all read</button>
                    </div>
                    <div class="notif-list" id="notifList">
                        <div style="padding:1.5rem;text-align:center;opacity:0.4;font-size:0.875rem">No notifications</div>
                    </div>
                </div>
            </div>

            <!-- User info -->
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
    if (container) {
        container.innerHTML = html;
    }

    // Top-bar bell integration (Admin/Scholar/Faculty dashboards often have a top bell)
    renderTopBell();

    // Start notification polling
    initNotifications();
    loadPendingBadge();
}

/**
 * renderTopBell — Hides the top-notif-container placeholder (bell is already in sidebar)
 */
function renderTopBell() {
    const container = document.getElementById('top-notif-container');
    if (!container) return;
    // Bell is already rendered in sidebar footer — just hide the duplicate slot
    container.style.display = 'none';
}

// ─────────────────────────────────────────────────────────
// NOTIFICATION SYSTEM
// ─────────────────────────────────────────────────────────
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
        renderNotifList(data.notifications);
    } catch (err) { }
}

function updateNotifBadge(count) {
    const badge = document.getElementById('notifBadge');
    if (!badge) return;
    if (count > 0) {
        badge.style.display = 'flex';
        badge.textContent = count > 99 ? '99+' : count;
    } else {
        badge.style.display = 'none';
    }
}

function renderNotifList(notifications) {
    const list = document.getElementById('notifList');
    if (!list) return;

    if (!notifications || notifications.length === 0) {
        list.innerHTML = `<div style="padding:2rem;text-align:center;opacity:0.4;font-size:0.875rem">No notifications yet</div>`;
        return;
    }

    const iconMap = {
        leave_approval    : '📋',
        publication       : '📄',
        meeting           : '📅',
        supervisor_request: '🎓',
        message           : '💬',
        milestone         : '🏁',
    };

    list.innerHTML = notifications.map(n => `
        <div class="notif-item ${n.is_read ? '' : 'unread'}" onclick="handleNotifClick(${n.id}, '${n.type}', ${n.related_id || 'null'})">
            <div class="notif-icon">${iconMap[n.type] || '🔔'}</div>
            <div class="notif-body">
                <p>${n.message}</p>
                <small>${n.created_at}</small>
            </div>
            ${!n.is_read ? '<span class="notif-dot"></span>' : ''}
        </div>
    `).join('');
}

function toggleNotifDropdown(e) {
    e.stopPropagation();
    const dropdown = document.getElementById('notifDropdown');
    if (dropdown) dropdown.classList.toggle('open');
}

document.addEventListener('click', () => {
    const dropdown = document.getElementById('notifDropdown');
    if (dropdown) dropdown.classList.remove('open');
});

async function handleNotifClick(notifId, type, relatedId) {
    try { await apiPut(`/notifications/${notifId}/read`); } catch(_) {}
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
        loadNotifications(user.id);
    } catch(_) {}
}

async function loadPendingBadge() {
    const user = getUser();
    if (!user) return;
    try {
        if (user.role === 'supervisor' || user.role === 'faculty') {
            // supervisor_id may be stored on user object; fallback to user.id
            const sv_id = user.supervisor_id || user.id;
            if (sv_id) {
                const leaves = await apiGet(`/supervisor/${sv_id}/leave-requests?status=pending`);
                const el = document.getElementById('badge-leave');
                if (el) {
                    const pending = Array.isArray(leaves) ? leaves.filter(l => l.status === 'pending') : [];
                    if (pending.length > 0) {
                        el.textContent = pending.length;
                        el.style.display = 'inline-block';
                    } else {
                        el.style.display = 'none';
                    }
                }
            }
        }
    } catch(_) {}
}

// ─────────────────────────────────────────────────────────
// GLOBAL HELPERS
// ─────────────────────────────────────────────────────────

function badgeClass(status) {
    if (!status) return 'badge-default';
    const s = status.toLowerCase();
    if (['approved', 'accepted', 'completed', 'active', 'published'].includes(s)) return 'badge-success';
    if (['rejected', 'failed', 'suspended', 'absent', 'debarred'].includes(s)) return 'badge-danger';
    if (['pending', 'under_review', 'in_progress'].includes(s)) return 'badge-warning';
    return 'badge-info';
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-IN', {
        day: 'numeric', month: 'short', year: 'numeric'
    });
}
