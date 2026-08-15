"""
Sidebar navigation + small shared layout widgets used across pages
(the project-scope selector, unread notification badge, etc.)
"""
import streamlit as st

from auth.auth_utils import current_user, logout_session
from database.db import session_scope
from database.models import Project, Notification
from config import APP_NAME
from utils.theme import get_colors, theme_toggle_button

import base64

NAV_SECTIONS = [
    ("Dashboard", "🏠"),
    ("Projects", "🏗️"),
    ("Client Requirement Analyzer", "📋"),
    ("Materials", "🧱"),
    ("BOQ Generator", "🧾"),
    ("Budget", "💰"),
    ("Workforce", "👷"),
    ("Equipment", "🚜"),
    ("Inventory", "📦"),
    ("Safety", "🦺"),
    ("AI Assistant", "🤖"),
    ("Analytics", "📊"),
    ("Reports", "📑"),
    ("Documents", "🗂️"),
]

BOTTOM_SECTIONS = [
    ("Notifications", "🔔"),
    ("Profile", "👤"),
]


@st.cache_data(ttl=15, show_spinner=False)
def _unread_notification_count():
    with session_scope() as db:
        return db.query(Notification).filter(Notification.is_read == False).count()  # noqa: E712


import os

@st.cache_data(show_spinner=False)
def _load_logo_b64(mtime=None):
    try:
        with open("assets/logo.jpg", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""


def render_sidebar():
    user = current_user()
    c = get_colors()
    logo_mtime = os.path.getmtime("assets/logo.jpg") if os.path.exists("assets/logo.jpg") else 0
    logo_b64 = _load_logo_b64(logo_mtime)

    logo_html = (
        f'<img src="data:image/jpeg;base64,{logo_b64}" style="width:30px;height:30px;border-radius:7px;object-fit:cover;flex-shrink:0;">'
        if logo_b64
        else f'<div class="cih-logo-mark">AI</div>'
    )

    with st.sidebar:
        st.markdown(
            f"""
            <div class="cih-brand-lockup">
                {logo_html}
                <div>
                    <div style="font-family:'Space Grotesk',sans-serif; font-weight:700; color:{c['text']}; font-size:0.92rem; line-height:1.1;">{APP_NAME}</div>
                    <div class="cih-muted" style="font-size:0.7rem;">Safety & Risk Analytics</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="cih-divider" style="margin: 0.6rem 0 0.8rem 0;"></div>', unsafe_allow_html=True)

        current_page = st.session_state.get("page", "Dashboard")

        st.markdown(f'<div style="font-size:0.65rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:{c["text_faint"]}; padding: 0 0.5rem 0.4rem 0.5rem; margin-top:0.2rem;">Management</div>', unsafe_allow_html=True)
        for label, icon in NAV_SECTIONS[:3]:
            is_active = current_page == label
            if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state["page"] = label
                st.rerun()
        
        st.markdown(f'<div style="font-size:0.65rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:{c["text_faint"]}; padding: 0.8rem 0.5rem 0.4rem 0.5rem;">Project Tools</div>', unsafe_allow_html=True)
        for label, icon in NAV_SECTIONS[3:]:
            is_active = current_page == label
            if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state["page"] = label
                st.rerun()

        st.markdown('<div class="cih-divider"></div>', unsafe_allow_html=True)

        unread = _unread_notification_count()
        notif_label = f"🔔  Notifications ({unread})" if unread else "🔔  Notifications"
        if st.button(notif_label, key="nav_Notifications", use_container_width=True,
                     type="primary" if current_page == "Notifications" else "secondary"):
            st.session_state["page"] = "Notifications"
            st.rerun()

        if st.button("👤  Profile", key="nav_Profile", use_container_width=True,
                     type="primary" if current_page == "Profile" else "secondary"):
            st.session_state["page"] = "Profile"
            st.rerun()

        if user.get("is_admin"):
            if st.button("🛠️  Admin Panel", key="nav_Admin", use_container_width=True,
                         type="primary" if current_page == "Admin Panel" else "secondary"):
                st.session_state["page"] = "Admin Panel"
                st.rerun()

        st.markdown('<div class="cih-divider"></div>', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:0.55rem; padding: 0 0.2rem;">
                <div style="width:32px;height:32px;border-radius:50%;background:{c['primary']};
                            display:flex;align-items:center;justify-content:center;color:{c['bg']};font-weight:700;font-size:0.8rem;">
                    {(user.get('full_name') or '?')[:1].upper()}
                </div>
                <div>
                    <div style="color:{c['text']}; font-size:0.85rem; font-weight:600;">{user.get('full_name','')}</div>
                    <div class="cih-muted" style="font-size:0.72rem;">{user.get('role','')}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        theme_toggle_button(key="sidebar_theme_toggle")
        if st.button("Logout", key="nav_logout", use_container_width=True):
            logout_session()
            st.rerun()


def project_selector(db, key="project_selector", include_archived=False, label="Project"):
    """Renders a selectbox of projects and returns the selected Project object (or None)."""
    q = db.query(Project)
    if not include_archived:
        q = q.filter(Project.is_archived == False)  # noqa: E712
    projects = q.order_by(Project.created_at.desc()).all()
    if not projects:
        st.info("No projects yet — create one from the Projects page first.")
        return None

    options = {f"{p.name} · {p.project_code}": p.id for p in projects}
    default_id = st.session_state.get("active_project_id")
    default_label = next((k for k, v in options.items() if v == default_id), list(options.keys())[0])

    chosen_label = st.selectbox(label, list(options.keys()), index=list(options.keys()).index(default_label), key=key)
    chosen_id = options[chosen_label]
    st.session_state["active_project_id"] = chosen_id
    return next(p for p in projects if p.id == chosen_id)
