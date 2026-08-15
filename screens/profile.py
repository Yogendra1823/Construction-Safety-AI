import streamlit as st

from database.db import session_scope
from database.models import User, ActivityLog
from auth.auth_utils import current_user, hash_password, login_session
from utils.styling import section_header, card_open, card_close


def render():
    section_header("Profile", "Manage your account details and preferences")

    user = current_user()
    tab_profile, tab_password, tab_activity = st.tabs(["👤 Profile", "🔒 Password", "📜 Activity"])

    with session_scope() as db:
        db_user = db.query(User).filter(User.id == user.get("id")).first()
        if not db_user:
            st.error("User not found.")
            return

        with tab_profile:
            with st.container(border=True):
                with st.form("edit_profile"):
                    c1, c2 = st.columns(2)
                    full_name = c1.text_input("Full Name", value=db_user.full_name)
                    email = c2.text_input("Email", value=db_user.email, disabled=True)
                    c3, c4 = st.columns(2)
                    phone = c3.text_input("Phone", value=db_user.phone or "")
                    department = c4.text_input("Department", value=db_user.department or "")
                    role = st.text_input("Role", value=db_user.role or "")
                    if st.form_submit_button("Save Changes", type="primary"):
                        db_user.full_name = full_name
                        db_user.phone = phone
                        db_user.department = department
                        db_user.role = role
                        db.flush()
                        login_session({
                            "id": db_user.id, "full_name": db_user.full_name, "email": db_user.email,
                            "role": db_user.role, "is_admin": db_user.is_admin, "department": db_user.department,
                        })
                        st.success("Profile updated.")
                        st.rerun()

        with tab_password:
            with st.container(border=True):
                with st.form("change_password"):
                    current_pw = st.text_input("Current Password", type="password")
                    new_pw = st.text_input("New Password", type="password")
                    confirm_pw = st.text_input("Confirm New Password", type="password")
                    if st.form_submit_button("Update Password", type="primary"):
                        from auth.auth_utils import verify_password
                        if not verify_password(current_pw, db_user.password_hash):
                            st.error("Current password is incorrect.")
                        elif len(new_pw) < 6:
                            st.error("New password must be at least 6 characters.")
                        elif new_pw != confirm_pw:
                            st.error("New passwords don't match.")
                        else:
                            db_user.password_hash = hash_password(new_pw)
                            db.flush()
                            st.success("Password updated.")

        with tab_activity:
            logs = db.query(ActivityLog).filter(ActivityLog.user_id == db_user.id).order_by(ActivityLog.created_at.desc()).limit(30).all()
            with st.container(border=True):
                if not logs:
                    st.caption("No activity recorded yet.")
                for l in logs:
                    st.markdown(f'<div class="cih-muted">• {l.action} — {l.created_at.strftime("%d %b %Y, %I:%M %p")}</div>', unsafe_allow_html=True)
