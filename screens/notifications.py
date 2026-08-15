import streamlit as st

from database.db import session_scope
from database.models import Notification, Project
from utils.styling import section_header, status_badge, card_open, card_close


def render():
    section_header("Notifications", "Budget alerts, low stock, delays, safety issues, and AI recommendations")

    with session_scope() as db:
        notifs = db.query(Notification).order_by(Notification.created_at.desc()).all()
        projects = {p.id: p for p in db.query(Project).all()}

        if st.button("Mark all as read"):
            for n in notifs:
                n.is_read = True
            st.rerun()

        if not notifs:
            st.info("No notifications yet.")
            return

        for n in notifs:
            kind = {"danger": "danger", "warning": "warning", "info": "info", "success": "success"}.get(n.severity, "neutral")
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    proj = projects.get(n.project_id)
                    st.markdown(f"{status_badge(n.notif_type, kind)} &nbsp; **{n.message}**", unsafe_allow_html=True)
                    sub = f"{proj.name} · " if proj else ""
                    st.caption(f"{sub}{n.created_at.strftime('%d %b %Y, %I:%M %p')}")
                with c2:
                    if not n.is_read:
                        if st.button("Mark read", key=f"read_{n.id}"):
                            n.is_read = True
                            st.rerun()
                    else:
                        st.caption("Read")
            st.write("")
