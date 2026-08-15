import pandas as pd
import streamlit as st

from database.db import session_scope
from database.models import User, Project, ActivityLog
from utils.styling import section_header, card_open, card_close


def render():
    from auth.auth_utils import current_user
    user = current_user()
    if not user.get("is_admin"):
        st.error("Access Denied: You do not have the required administrative privileges to view this page.")
        st.stop()

    section_header("Admin Panel", "Users, roles, projects, and system logs")

    tab_users, tab_projects, tab_logs, tab_system = st.tabs(["👥 Users", "🏗️ Projects", "📜 Logs", "⚙️ System"])

    with session_scope() as db:
        with tab_users:
            users = db.query(User).all()
            with st.container(border=True):
                df = pd.DataFrame([{
                    "Name": u.full_name, "Email": u.email, "Role": u.role,
                    "Department": u.department, "Admin": u.is_admin,
                    "Last Login": u.last_login.strftime("%d %b %Y") if u.last_login else "Never",
                } for u in users])
                st.dataframe(df, use_container_width=True, hide_index=True)

            st.write("")
            with st.expander("Manage Users (Edit / Delete)"):
                target_name = st.selectbox("Select User to Manage", [u.full_name for u in users])
                target_user = next((u for u in users if u.full_name == target_name), None)
                if target_user:
                    c1, c2 = st.columns(2)
                    with c1:
                        new_name = st.text_input("Full Name", value=target_user.full_name)
                        new_email = st.text_input("Email", value=target_user.email)
                        new_role = st.text_input("Role", value=target_user.role or "")
                    with c2:
                        new_dept = st.text_input("Department", value=target_user.department or "")
                        make_admin = st.checkbox("Grant admin access", value=target_user.is_admin)
                    
                    st.write("")
                    new_password = st.text_input("Reset Password (leave blank to keep current)", type="password")
                    
                    st.write("")
                    col_save, col_delete = st.columns(2)
                    with col_save:
                        if st.button("Save Changes", type="primary", use_container_width=True):
                            target_user.full_name = new_name
                            target_user.email = new_email
                            target_user.role = new_role
                            target_user.department = new_dept
                            target_user.is_admin = make_admin
                            if new_password.strip():
                                from auth.auth_utils import hash_password, validate_password_complexity
                                is_valid, msg = validate_password_complexity(new_password.strip())
                                if not is_valid:
                                    st.error(msg)
                                else:
                                    target_user.password_hash = hash_password(new_password.strip())
                                    db.commit()
                                    st.success(f"Updated {target_user.full_name}.")
                                    st.rerun()
                            else:
                                db.commit()
                                st.success(f"Updated {target_user.full_name}.")
                                st.rerun()
                    with col_delete:
                        if st.button("Delete User", use_container_width=True): 
                            # Phase 3 Hardening: Manual nullification is no longer needed.
                            # The robust SQLAlchemy cascades configured in database/models.py
                            # will securely and automatically handle deleting the user's assignments
                            # and nullifying their reference in projects/logs/etc.
                            db.delete(target_user)
                            db.commit()
                            st.success(f"Deleted user {target_name}.")
                            st.rerun()

        with tab_projects:
            projects = db.query(Project).all()
            with st.container(border=True):
                df_p = pd.DataFrame([{
                    "Code": p.project_code, "Name": p.name, "Status": p.status,
                    "Progress": f"{p.progress_percent:.0f}%", "Archived": p.is_archived,
                } for p in projects])
                st.dataframe(df_p, use_container_width=True, hide_index=True)

        with tab_logs:
            logs = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(100).all()
            with st.container(border=True):
                if not logs:
                    st.caption("No activity yet.")
                for l in logs:
                    st.markdown(f'<div class="cih-muted">• {l.action} — {l.created_at.strftime("%d %b %Y, %I:%M %p")}</div>', unsafe_allow_html=True)

        with tab_system:
            with st.container(border=True):
                section_header("Demo Data")
                st.caption("Reset the database and reload realistic demo data — useful for presentations or testing.")
                confirm = st.checkbox("I understand this will erase all current data")
                if st.button("🔄 Reset & Load Demo Data", disabled=not confirm, type="primary"):
                    from database.seed import seed_demo_data
                    ok, msg = seed_demo_data(force=True)
                    st.success(msg)
                    st.rerun()

            st.write("")
            with st.container(border=True):
                section_header("About")
                from config import APP_FULL_NAME, APP_VERSION
                st.caption(f"{APP_FULL_NAME} · v{APP_VERSION} · Streamlit + SQLAlchemy + MySQL")
