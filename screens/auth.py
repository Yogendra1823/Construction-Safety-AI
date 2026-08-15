import streamlit as st
import base64
import os
from database.db import session_scope
from database.models import User
from auth.auth_utils import authenticate_user, login_session, hash_password
from config import APP_FULL_NAME


@st.cache_data(show_spinner=False)
def load_image_as_base64(path, mtime=None):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""


def render():
    logo_mtime = os.path.getmtime("assets/logo.jpg") if os.path.exists("assets/logo.jpg") else 0
    bg_mtime   = os.path.getmtime("assets/login_bg.jpg") if os.path.exists("assets/login_bg.jpg") else 0
    logo_b64   = load_image_as_base64("assets/logo.jpg", logo_mtime)
    bg_b64     = load_image_as_base64("assets/login_bg.jpg", bg_mtime)

    st.markdown(f"""
    <style>
    /* Hide Streamlit header/footer and sidebar completely on login screen */
    header {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    section[data-testid="stSidebar"] {{ display: none !important; }}
    button[kind="header"] {{ display: none !important; }}
    
    /* Full screen background image on the main app wrapper */
    .stApp {{
        background: linear-gradient(rgba(14,17,23,0.5), rgba(14,17,23,0.85)), url('data:image/jpeg;base64,{bg_b64}');
        background-size: cover;
        background-position: center;
        background-attachment: scroll;
    }}
    
    /* Transform the main block container into a beautiful floating glass card */
    .block-container {{
        background: rgba(14, 17, 23, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
        padding: 4rem 4rem !important;
        max-width: 900px !important;
        margin-top: 8vh;
        margin-bottom: 8vh;
    }}
    
    /* OVERRIDE GLOBAL STYLING: Remove nested borders */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]::before, 
    div[data-testid="stVerticalBlockBorderWrapper"]::after {{
        display: none !important;
    }}
    div[data-testid="stForm"] {{
        border: none !important;
        padding: 0 !important;
    }}
    
    /* Typography */
    .hero-title {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3.2rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 1rem;
        background: linear-gradient(100deg, #fff 20%, #a8d8f0 40%, #fff 60%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: heroShimmer 4s linear infinite;
    }}
    @keyframes heroShimmer {{
        0% {{ background-position: 200% center; }}
        100% {{ background-position: -200% center; }}
    }}
    .hero-subtitle {{
        font-size: 1.05rem;
        color: rgba(255,255,255,0.7);
        margin-bottom: 2rem;
        line-height: 1.5;
    }}
    
    .auth-header {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: white;
    }}
    .auth-subheader {{
        color: #999;
        margin-bottom: 2rem;
        font-size: 1rem;
    }}
    
    .feature-list {{
        list-style: none;
        padding: 0;
    }}
    .feature-list li {{
        font-size: 1rem;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        color: rgba(255,255,255,0.8);
    }}
    .feature-list li::before {{
        content: '•';
        color: #4da8da;
        font-weight: bold;
        margin-right: 12px;
        font-size: 1.5rem;
    }}

    /* Inputs inside glass card */
    .stTextInput input, .stSelectbox select {{
        background: #1C2433 !important;
        border: 1px solid #334155 !important;
        color: #F8FAFC !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
    }}
    .stTextInput input:focus {{
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25) !important;
    }}
    div[data-testid="stCheckbox"] label span {{
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
    }}

    /* Buttons */
    .stButton > button[kind="primary"] {{
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4) !important;
    }}
    .stButton > button:not([kind="primary"]) {{
        background: #1E293B !important;
        color: #CBD5E1 !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "login"

    col_left, col_divider, col_right = st.columns([1.2, 0.1, 1])

    logo_img_html = (
        f'<img src="data:image/jpeg;base64,{logo_b64}" width="65" style="border-radius:14px; margin-bottom: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.4); object-fit: cover;">'
        if logo_b64
        else '<div style="width:65px;height:65px;border-radius:14px;background:#2563EB;margin-bottom:2rem;display:flex;align-items:center;justify-content:center;font-family:\'Space Grotesk\';font-weight:700;color:white;font-size:1.4rem;box-shadow:0 4px 12px rgba(37,99,235,0.4);">AI</div>'
    )

    with col_left:
        st.markdown(f"""
        <div>
            {logo_img_html}
            <div class="hero-title">Build Smarter.<br>Deliver Faster.</div>
            <div class="hero-subtitle">Agentic AI platform for safety monitoring and construction risk analytics. Real-time site surveillance and predictive analytics.</div>
            <ul class="feature-list">
                <li>Real-time Safety Incident Monitoring</li>
                <li>Construction Cost &amp; Risk Analytics</li>
                <li>Executive Command Center</li>
                <li>Smart Resource &amp; Material Tracking</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_divider:
        st.markdown('''
        <div style="height: 100%; min-height: 400px; width: 1px; background: rgba(255,255,255,0.1); margin: 0 auto;"></div>
        ''', unsafe_allow_html=True)

    with col_right:
        if st.session_state["auth_mode"] == "login":
            st.markdown('<div class="auth-header">Welcome Back</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-subheader">Sign in to your Agentic AI workspace</div>', unsafe_allow_html=True)
            
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Work Email")
                password = st.text_input("Password", type="password")
                remember = st.checkbox("Remember me", value=True)
                submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
                
                if submitted:
                    with st.spinner("Authenticating securely..."):
                        ok, user = authenticate_user(email, password)
                    if ok:
                        login_session(user)
                        st.session_state["page"] = "Dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
            
            st.write("")
            st.markdown("<p style='text-align:center; color:#888;'>Don't have an account?</p>", unsafe_allow_html=True)
            if st.button("Create an Account", use_container_width=True):
                st.session_state["auth_mode"] = "register"
                st.rerun()

        elif st.session_state["auth_mode"] == "register":
            st.markdown('<div class="auth-header">Create Account</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-subheader">Register a new Agentic AI workspace account</div>', unsafe_allow_html=True)
            
            with st.form("register_form"):
                full_name = st.text_input("Full Name")
                email = st.text_input("Work Email")
                role = st.selectbox("Role", ["Project Manager", "Site Engineer", "Contractor", "Executive", "Other"])
                department = st.text_input("Department")
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button("Register Now", type="primary", use_container_width=True)
                
                if submitted:
                    if not full_name or not email or not password:
                        st.error("Please fill in all required fields.")
                    elif password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        with st.spinner("Creating enterprise account..."):
                            reg_error = None
                            auto_login_user = None
                            with session_scope() as db:
                                exists = db.query(User).filter(User.email == email).first()
                                if exists:
                                    reg_error = "Email is already registered."
                                else:
                                    from auth.auth_utils import validate_password_complexity
                                    is_valid, msg = validate_password_complexity(password)
                                    if not is_valid:
                                        reg_error = msg
                                    else:
                                        new_user = User(
                                            full_name=full_name,
                                            email=email,
                                            password_hash=hash_password(password),
                                            role=role,
                                            department=department
                                        )
                                        db.add(new_user)
                                        auto_login_user = (email, password)
                            if reg_error:
                                st.error(reg_error)
                            elif auto_login_user:
                                ok, u = authenticate_user(*auto_login_user)
                                if ok:
                                    login_session(u)
                                    st.session_state["page"] = "Dashboard"
                                    st.rerun()
            
            st.write("")
            st.markdown("<p style='text-align:center; color:#888;'>Already have an account?</p>", unsafe_allow_html=True)
            if st.button("Sign In", use_container_width=True):
                st.session_state["auth_mode"] = "login"
                st.rerun()
