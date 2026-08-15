"""
Theme state. The whole app reads colors through get_colors() rather than a
static import, so a single toggle switches every page, chart, and component
between dark and light instantly — no page reload, no per-page logic.
"""
import streamlit as st

from config import COLOR_THEMES, DEFAULT_THEME


def get_theme() -> str:
    return st.session_state.get("theme", DEFAULT_THEME)


def get_colors() -> dict:
    return COLOR_THEMES[get_theme()]


def set_theme(theme: str):
    if theme in COLOR_THEMES:
        st.session_state["theme"] = theme


def toggle_theme():
    st.session_state["theme"] = "light" if get_theme() == "dark" else "dark"


def theme_toggle_button(key: str = "theme_toggle_btn"):
    """Renders a small icon button that flips the theme on click. Safe to
    call from multiple places (sidebar, auth screens) — each needs a unique
    key."""
    icon = "☀️" if get_theme() == "dark" else "🌙"
    label = "Light mode" if get_theme() == "dark" else "Dark mode"
    if st.button(f"{icon} {label}", key=key, use_container_width=True):
        toggle_theme()
        st.rerun()
