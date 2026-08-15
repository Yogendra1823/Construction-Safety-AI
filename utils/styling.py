"""
"Site Blueprint" design system. The whole visual identity — a faint
blueprint grid, corner-bracket cards like technical-drawing registration
marks, and monospace data readouts — is built once here and shared by
every page. Every color comes from utils.theme.get_colors() (never a
static import) so the dark/light toggle affects the entire app instantly.
"""
import streamlit as st
from utils.theme import get_colors, get_theme


def inject_css():
    c = get_colors()
    theme = get_theme()

    # Precise shadow scale based on theme
    shadow_sm  = f"0 1px 3px {c['shadow']}, 0 1px 2px {c['shadow']}"
    shadow_md  = f"0 4px 6px -1px {c['shadow']}, 0 2px 4px -2px {c['shadow']}"
    shadow_lg  = f"0 10px 15px -3px {c['shadow']}, 0 4px 6px -4px {c['shadow']}"
    shadow_xl  = f"0 20px 25px -5px {c['shadow']}, 0 8px 10px -6px {c['shadow']}"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;1,14..32,400&family=JetBrains+Mono:wght@400;500&display=swap');

        /* ═══════════════════════════ RESET & BASE ═══════════════════════════ */
        *, *::before, *::after {{ box-sizing: border-box; }}

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-feature-settings: "cv02","cv03","cv04","cv11";
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        h1, h2, h3, h4, h5, h6, .cih-display {{
            font-family: 'Space Grotesk', sans-serif;
            letter-spacing: -0.02em;
            font-weight: 600;
        }}
        .cih-mono {{ font-family: 'JetBrains Mono', monospace; font-size: 0.875em; }}

        /* ═══════════════════════════ CHROME ════════════════════════════════ */
        .stApp {{ background: {c['bg']}; color: {c['text']}; }}
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        header[data-testid="stHeader"] {{ background: transparent; box-shadow: none; }}

        /* Remove the Streamlit top padding */
        .block-container {{
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 100% !important;
        }}

        /* ═══════════════════════════ SIDEBAR ═══════════════════════════════ */
        section[data-testid="stSidebar"] {{
            background: {c['bg_card']} !important;
            border-right: 1px solid {c['border']} !important;
            width: 240px !important;
        }}
        section[data-testid="stSidebar"] > div {{
            padding: 1rem 0.75rem !important;
        }}

        /* All sidebar buttons */
        section[data-testid="stSidebar"] .stButton button {{
            width: 100%;
            text-align: left;
            background: transparent;
            border: none;
            color: {c['text_dim']};
            font-size: 0.875rem;
            font-weight: 500;
            padding: 0.5rem 0.75rem;
            border-radius: 8px;
            margin-bottom: 2px;
            transition: background 0.15s ease, color 0.15s ease;
            letter-spacing: 0;
            line-height: 1.4;
        }}
        section[data-testid="stSidebar"] .stButton button:hover {{
            background: {c['primary']}12;
            color: {c['primary']};
        }}
        /* Active nav pill */
        section[data-testid="stSidebar"] .stButton button[kind="primary"] {{
            background: {c['primary']}18 !important;
            color: {c['primary']} !important;
            font-weight: 600 !important;
            box-shadow: none !important;
        }}
        section[data-testid="stSidebar"] .stButton button[kind="primary"]:hover {{
            background: {c['primary']}25 !important;
        }}

        /* ═══════════════════════════ CARDS ══════════════════════════════════ */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {c['bg_card']} !important;
            border: 1px solid {c['border']} !important;
            border-radius: 12px !important;
            padding: 1rem 1rem 0.75rem 1rem !important;
            box-shadow: {shadow_sm} !important;
            transition: box-shadow 0.2s ease, border-color 0.2s ease;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
            box-shadow: {shadow_md} !important;
            border-color: {c['primary']}40 !important;
        }}

        /* ═══════════════════════════ KPI CARDS ═════════════════════════════ */
        .cih-kpi {{
            background: {c['bg_card']};
            border: 1px solid {c['border']};
            border-radius: 12px;
            padding: 1.25rem 1.25rem 1rem 1.25rem;
            height: 100%;
            will-change: transform;
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: {shadow_sm};
        }}
        .cih-kpi:hover {{
            transform: translateY(-2px);
            box-shadow: {shadow_md};
            border-color: var(--accent, {c['primary']})55;
        }}
        .cih-kpi-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.75rem;
        }}
        .cih-kpi-label {{
            color: {c['text_dim']};
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.07em;
        }}
        .cih-kpi-icon {{
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: var(--accent, {c['primary']})15;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
        }}
        .cih-kpi-value {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.9rem;
            font-weight: 700;
            color: {c['text']};
            line-height: 1;
            margin-bottom: 0.35rem;
            letter-spacing: -0.02em;
        }}
        .cih-kpi-delta {{
            font-size: 0.78rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}
        .cih-kpi-sparkline {{ margin-top: 0.85rem; opacity: 0.9; }}

        /* ═══════════════════════════ BADGES ════════════════════════════════ */
        .cih-badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.2rem 0.55rem;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            letter-spacing: 0.01em;
            line-height: 1.5;
        }}

        /* ═══════════════════════════ SECTION HEADERS ═══════════════════════ */
        .cih-section-title {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1rem;
            font-weight: 600;
            color: {c['text']};
            margin-bottom: 0.15rem;
            letter-spacing: -0.01em;
        }}
        .cih-section-subtitle {{
            color: {c['text_dim']};
            font-size: 0.8rem;
            margin-bottom: 0.9rem;
            font-weight: 400;
        }}
        .cih-divider {{ border: none; border-top: 1px solid {c['border']}; margin: 0.9rem 0; }}
        .cih-muted {{ color: {c['text_dim']}; font-size: 0.82rem; line-height: 1.5; }}

        /* Brand lockup in sidebar */
        .cih-brand-lockup {{ display:flex; align-items:center; gap:0.6rem; padding: 0.25rem 0.5rem 0.75rem; }}
        .cih-logo-mark {{
            width: 30px; height: 30px; border-radius: 7px;
            background: linear-gradient(135deg, {c['primary']}, {c['primary_dark']});
            display:flex; align-items:center; justify-content:center;
            font-family:'Space Grotesk'; font-weight:700; color:#fff; font-size:0.8rem;
            box-shadow: 0 2px 6px {c['primary']}40;
            flex-shrink: 0;
        }}

        /* ═══════════════════════════ INPUTS & FORMS ════════════════════════ */
        .stTextInput input, .stNumberInput input, .stTextArea textarea, .stDateInput input {{
            background: {c['bg_card']} !important;
            border: 1px solid {c['border']} !important;
            color: {c['text']} !important;
            border-radius: 8px !important;
            font-size: 0.875rem !important;
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }}
        .stTextInput input:focus, .stNumberInput input:focus,
        .stTextArea textarea:focus, .stDateInput input:focus {{
            border-color: {c['primary']} !important;
            box-shadow: 0 0 0 3px {c['primary']}20 !important;
            outline: none !important;
        }}
        div[data-baseweb="select"] > div {{
            background: {c['bg_card']} !important;
            border-color: {c['border']} !important;
            border-radius: 8px !important;
            font-size: 0.875rem !important;
        }}
        div[data-testid="stForm"] {{
            background: transparent;
            border: none !important;
            padding: 0 !important;
        }}

        /* ═══════════════════════════ BUTTONS ═══════════════════════════════ */
        .stButton > button[kind="primary"] {{
            background: {c['primary']} !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-size: 0.875rem !important;
            font-weight: 600 !important;
            padding: 0.5rem 1rem !important;
            box-shadow: 0 1px 3px {c['primary']}50 !important;
            transition: background 0.15s ease, box-shadow 0.15s ease, transform 0.1s ease;
            letter-spacing: 0;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: {c['primary_dark']} !important;
            box-shadow: 0 4px 12px {c['primary']}40 !important;
            transform: translateY(-1px);
        }}
        .stButton > button:not([kind="primary"]) {{
            background: {c['bg_card_alt']} !important;
            border: 1px solid {c['border']} !important;
            color: {c['text']} !important;
            border-radius: 8px !important;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            transition: background 0.15s ease, border-color 0.15s ease;
        }}
        .stButton > button:not([kind="primary"]):hover {{
            background: {c['bg_card']} !important;
            border-color: {c['primary']}60 !important;
        }}

        /* ═══════════════════════════ DATAFRAMES ════════════════════════════ */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {c['border']};
            border-radius: 10px;
            overflow: hidden;
            box-shadow: {shadow_sm};
        }}

        /* ═══════════════════════════ TABS ══════════════════════════════════ */
        div[data-testid="stTabs"] > div:first-child {{
            border-bottom: 1px solid {c['border']};
            gap: 0;
        }}
        button[data-testid="stTab"] {{
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            color: {c['text_dim']} !important;
            padding: 0.6rem 1rem !important;
            border-bottom: 2px solid transparent !important;
            transition: color 0.15s ease, border-color 0.15s ease;
        }}
        button[data-testid="stTab"][aria-selected="true"] {{
            color: {c['primary']} !important;
            border-bottom-color: {c['primary']} !important;
            font-weight: 600 !important;
        }}
        button[data-testid="stTab"]:hover {{
            color: {c['text']} !important;
        }}

        /* ═══════════════════════════ PROGRESS BARS ═════════════════════════ */
        div[data-testid="stProgress"] > div {{
            background: {c['border']};
            border-radius: 999px;
            overflow: hidden;
        }}
        div[data-testid="stProgress"] > div > div {{
            background: linear-gradient(90deg, {c['primary']}, {c['primary_dark']});
            border-radius: 999px;
            transition: width 0.4s ease;
        }}

        /* ═══════════════════════════ ALERTS ════════════════════════════════ */
        div[data-testid="stAlert"] {{
            border-radius: 10px !important;
            border-left-width: 3px !important;
            font-size: 0.875rem !important;
        }}

        /* ═══════════════════════════ SELECTBOX DROPDOWN ════════════════════ */
        ul[data-testid="stSelectboxVirtualDropdown"] {{
            background: {c['bg_card']} !important;
            border: 1px solid {c['border']} !important;
            border-radius: 10px !important;
            box-shadow: {shadow_lg} !important;
        }}

        /* ═══════════════════════════ CHAT WIDGET ═══════════════════════════ */
        /* Floating button positioning */
        div[data-testid="stVerticalBlock"] > div:has(.cih-float-anchor) ~ div {{
            position: fixed !important;
            bottom: 24px;
            right: 24px;
            z-index: 99999;
            width: fit-content !important;
        }}

        /* The FAB button */
        div[data-testid="stVerticalBlock"] > div:has(.cih-float-anchor) ~ div button {{
            border-radius: 50% !important;
            width: 56px !important;
            height: 56px !important;
            min-height: 56px !important;
            font-size: 1.5rem !important;
            box-shadow: {shadow_lg} !important;
            background: {c['primary']} !important;
            border: none !important;
            color: #FFFFFF !important;
            transition: transform 0.2s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.2s ease !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        div[data-testid="stVerticalBlock"] > div:has(.cih-float-anchor) ~ div button:hover {{
            transform: scale(1.08) !important;
            box-shadow: {shadow_xl} !important;
        }}

        /* Popover panel */
        div[data-testid="stPopoverBody"]:has(.cih-popover-anchor) {{
            position: fixed !important;
            bottom: 88px !important;
            right: 24px !important;
            left: auto !important;
            top: auto !important;
            transform: none !important;
            width: 380px !important;
            max-height: calc(100vh - 120px) !important;
            height: 540px !important;
            border-radius: 16px !important;
            background: {c['bg_card']} !important;
            border: 1px solid {c['border']} !important;
            box-shadow: {shadow_xl} !important;
            padding: 0 !important;
            overflow: auto !important;
            animation: popIn 0.2s cubic-bezier(0.34,1.56,0.64,1) forwards;
            transform-origin: bottom right;
        }}

        /* Scrollbar inside chat */
        div[data-testid="stPopoverBody"]:has(.cih-popover-anchor)::-webkit-scrollbar {{ width: 4px; }}
        div[data-testid="stPopoverBody"]:has(.cih-popover-anchor)::-webkit-scrollbar-track {{ background: transparent; }}
        div[data-testid="stPopoverBody"]:has(.cih-popover-anchor)::-webkit-scrollbar-thumb {{
            background: {c['border']};
            border-radius: 4px;
        }}

        .cih-float-anchor, .cih-popover-anchor {{ display: none !important; }}

        @keyframes popIn {{
            0%   {{ opacity: 0; transform: scale(0.88) translateY(12px); }}
            100% {{ opacity: 1; transform: scale(1) translateY(0); }}
        }}

        /* ═══════════════════════════ CHAT MESSAGES ══════════════════════════ */
        div[data-testid="stChatMessage"] {{
            background: transparent !important;
            border: none !important;
            padding: 0.25rem 0 !important;
        }}

        /* ═══════════════════════════ SPINNER ══════════════════════════════ */
        div[data-testid="stSpinner"] {{ color: {c['primary']}; }}

        /* ═══════════════════════════ SLIDER ═══════════════════════════════ */
        div[data-testid="stSlider"] > div > div > div {{
            background: {c['primary']} !important;
        }}

        /* ═══════════════════════════ CHECKBOX ══════════════════════════════ */
        div[data-testid="stCheckbox"] input:checked + div {{
            background: {c['primary']} !important;
            border-color: {c['primary']} !important;
        }}

        /* ═══════════════════════════ SIDEBAR SCROLLBAR ══════════════════════ */
        section[data-testid="stSidebar"]::-webkit-scrollbar {{ width: 3px; }}
        section[data-testid="stSidebar"]::-webkit-scrollbar-track {{ background: transparent; }}
        section[data-testid="stSidebar"]::-webkit-scrollbar-thumb {{ background: {c['border']}; border-radius: 3px; }}

        /* ═══════════════════════════ CAPTION / SMALL ═══════════════════════ */
        .stCaption, [data-testid="stCaptionContainer"] {{
            color: {c['text_faint']} !important;
            font-size: 0.75rem !important;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label, value, icon="", accent="primary", delta=None, delta_kind="neutral", sparkline_data=None):
    c = get_colors()
    color = c.get(accent, c["primary"])
    
    delta_html = ""
    if delta:
        delta_color = {"up": c["success"], "down": c["danger"], "neutral": c["text_dim"]}.get(delta_kind, c["text_dim"])
        arrow = {"up": "↑", "down": "↓", "neutral": "−"}.get(delta_kind, "")
        delta_html = f'<div class="cih-kpi-delta" style="color:{delta_color}"><span>{arrow}</span> {delta}</div>'

    sparkline_html = ""
    if sparkline_data and len(sparkline_data) > 1:
        max_val = max(sparkline_data)
        min_val = min(sparkline_data)
        width, height = 100, 24
        points = []
        for i, val in enumerate(sparkline_data):
            x = (i / (len(sparkline_data) - 1)) * width
            y = height - (((val - min_val) / (max_val - min_val)) * height) if max_val > min_val else height/2
            points.append(f"{x},{y}")
        polyline = " ".join(points)
        sparkline_html = f'''
        <div class="cih-kpi-sparkline">
            <svg width="100%" height="{height}" viewBox="0 0 {width} {height}" preserveAspectRatio="none">
                <polyline fill="none" stroke="{color}" stroke-width="2" points="{polyline}" vector-effect="non-scaling-stroke"/>
            </svg>
        </div>'''

    st.markdown(
        f"""
        <div class="cih-kpi" style="--accent: {color}">
            <div class="cih-kpi-top">
                <div class="cih-kpi-label">{label}</div>
                <div class="cih-kpi-icon">{icon}</div>
            </div>
            <div class="cih-kpi-value">{value}</div>
            {delta_html}
            {sparkline_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(text, kind="neutral"):
    c = get_colors()
    palette = {
        "success": (c["success"], f"{c['success']}22"),
        "warning": (c["warning"], f"{c['warning']}22"),
        "danger": (c["danger"], f"{c['danger']}22"),
        "info": (c["primary"], f"{c['primary']}22"),
        "neutral": (c["text_dim"], c["bg_card_alt"]),
    }
    fg, bg = palette.get(kind, palette["neutral"])
    return f'<span class="cih-badge" style="color:{fg}; background:{bg}; border:1px solid {fg}55;">{text}</span>'


def status_kind_for_project(status: str) -> str:
    return {
        "Completed": "success",
        "Ongoing": "info",
        "Planning": "neutral",
        "On Hold": "warning",
        "Delayed": "danger",
    }.get(status, "neutral")


def section_header(title, subtitle=None):
    sub = f'<div class="cih-section-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="cih-section-title">{title}</div>{sub}', unsafe_allow_html=True)


def card_open():
    st.markdown('<div class="cih-card">', unsafe_allow_html=True)


def card_close():
    st.markdown("</div>", unsafe_allow_html=True)
