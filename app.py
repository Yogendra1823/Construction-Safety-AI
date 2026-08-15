"""
Construction Intelligence Hub — main entry point.

Run with:  streamlit run app.py
"""
import streamlit as st

from config import APP_NAME, APP_FULL_NAME, APP_TAGLINE
from utils.styling import inject_css, section_header, card_open, card_close
from utils.theme import theme_toggle_button
from auth.auth_utils import (
    is_authenticated, authenticate_user, register_user, reset_password,
    login_session, current_user,
)
from database.db import session_scope
from database.models import User

st.set_page_config(page_title=APP_NAME, page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

inject_css()

if "auth_page" not in st.session_state:
    st.session_state["auth_page"] = "landing"
if "page" not in st.session_state:
    st.session_state["page"] = "Dashboard"





# ================================================================ ROUTING --
def render_app():
    from utils.layout import render_sidebar
    render_sidebar()

    page = st.session_state.get("page", "Dashboard")

    if page == "Dashboard":
        from screens import dashboard as mod
    elif page == "Projects":
        from screens import projects as mod
    elif page == "Client Requirement Analyzer":
        from screens import client_requirement_analyzer as mod
    elif page == "Materials":
        from screens import materials as mod
    elif page == "BOQ Generator":
        from screens import boq_generator as mod
    elif page == "Budget":
        from screens import budget as mod
    elif page == "Workforce":
        from screens import workforce as mod
    elif page == "Equipment":
        from screens import equipment as mod
    elif page == "Inventory":
        from screens import inventory as mod
    elif page == "Safety":
        from screens import safety as mod
    elif page == "AI Assistant":
        from screens import ai_assistant as mod
    elif page == "Analytics":
        from screens import analytics as mod
    elif page == "Reports":
        from screens import reports as mod
    elif page == "Documents":
        from screens import documents as mod
    elif page == "Notifications":
        from screens import notifications as mod
    elif page == "Profile":
        from screens import profile as mod
    elif page == "Admin Panel":
        from screens import admin_panel as mod
    else:
        from screens import dashboard as mod

    mod.render()

    if page != "AI Assistant":
        _render_floating_chat()


def _render_floating_chat():
    from utils.chat_widget import render_chat_ui
    with st.container():
        st.markdown('<div class="cih-float-anchor"></div>', unsafe_allow_html=True)
        with st.popover("💬", use_container_width=False):
            st.markdown('<div class="cih-popover-anchor"></div>', unsafe_allow_html=True)
            render_chat_ui("floating", project_id=st.session_state.get("active_project_id"), height=450)


# =================================================================== MAIN --
if is_authenticated():
    render_app()
else:
    from screens import auth as mod
    mod.render()
