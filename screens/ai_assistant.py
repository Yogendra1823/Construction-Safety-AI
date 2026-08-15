import plotly.graph_objects as go
import streamlit as st

from database.db import session_scope
from database.models import MaterialItem, BudgetItem, SafetyIncident
from ai_engine.chatbot import answer_question
from ai_engine import llm_client
from config import OLLAMA_MODEL
from ai_engine.delay_predictor import predict_delay_risk
from ai_engine.cost_predictor import predict_budget_overrun_risk
from ai_engine.risk_analyzer import compute_project_risk, material_shortage_risk, safety_risk_score
from ai_engine.recommendation_engine import generate_recommendations
from utils.layout import project_selector
from utils.styling import section_header, status_badge, card_open, card_close
from utils.charts import apply_dark_theme, CHART_COLORWAY


def render():
    section_header("AI Assistant", "Ask questions, review risk, and get recommendations — grounded in live project data")

    tab_chat, tab_risk, tab_recs, tab_delay = st.tabs(["💬 Chat", "🧠 Risk Analysis", "💡 Recommendations", "⏱️ Delay Predictor"])

    with tab_chat:
        with session_scope() as db:
            project = project_selector(db, key="ai_chat_project")
            project_id = project.id if project else None

        if llm_client.is_available():
            st.markdown(status_badge(f"🟢 {OLLAMA_MODEL} connected — Enterprise AI Core online", "success"), unsafe_allow_html=True)
        else:
            st.markdown(status_badge(f"🔴 {OLLAMA_MODEL} offline — AI capabilities disabled", "danger"), unsafe_allow_html=True)
            st.caption("Please ensure Ollama is installed and running with `ollama pull gemma3:1b`.")

        from utils.chat_widget import render_chat_ui
        render_chat_ui("ai_assistant_page", project_id=project_id, height=600)

    with tab_risk:
        with session_scope() as db:
            project = project_selector(db, key="ai_risk_project")
            if not project:
                return
            materials = db.query(MaterialItem).filter(MaterialItem.project_id == project.id).all()
            budget_items = db.query(BudgetItem).filter(BudgetItem.project_id == project.id).all()
            incidents = db.query(SafetyIncident).filter(SafetyIncident.project_id == project.id).all()

            budget_risk, _ = predict_budget_overrun_risk(project.budget_total, project.budget_used, project.progress_percent)
            delay_risk, delay_level, expected_pct = predict_delay_risk(project.start_date, project.expected_completion, project.progress_percent)
            mat_risk = material_shortage_risk(materials)
            saf_risk = safety_risk_score(incidents)
            composite, level, breakdown = compute_project_risk(budget_risk, delay_risk, mat_risk, saf_risk)

            accent = {"Low": "success", "Moderate": "warning", "High": "danger", "Critical": "danger"}.get(level, "warning")
            st.write("")
            col1, col2 = st.columns([1, 1.4])
            with col1:
                with st.container(border=True):
                    section_header("Composite AI Risk Score")
                    st.markdown(f'<div style="font-family:Space Grotesk,sans-serif; font-size:2.4rem; font-weight:700;">{composite}/100</div>', unsafe_allow_html=True)
                    st.markdown(status_badge(f"{level} Risk", accent), unsafe_allow_html=True)
                    st.caption(f"Schedule is at {project.progress_percent:.0f}% vs. an expected {expected_pct:.0f}% for this point in the timeline.")
            with col2:
                with st.container(border=True):
                    section_header("Risk Breakdown")
                    fig = go.Figure(data=[go.Bar(
                        x=["Budget", "Delay", "Material", "Safety"],
                        y=[breakdown["budget_risk"], breakdown["delay_risk"], breakdown["material_risk"], breakdown["safety_risk"]],
                        marker_color=CHART_COLORWAY[:4],
                    )])
                    fig.update_layout(yaxis_range=[0, 100])
                    apply_dark_theme(fig, height=260, show_legend=False)
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with tab_recs:
        @st.cache_data(ttl=300, show_spinner="Gathering AI recommendations...")
        def _get_cached_recs(proj_id):
            with session_scope() as db:
                from database.models import Project
                proj = db.get(Project, proj_id)
                if not proj: return []
                mats = db.query(MaterialItem).filter(MaterialItem.project_id == proj.id).all()
                budgets = db.query(BudgetItem).filter(BudgetItem.project_id == proj.id).all()
                d_risk, d_level, _ = predict_delay_risk(proj.start_date, proj.expected_completion, proj.progress_percent)
                return generate_recommendations(proj, mats, budgets, d_level, d_risk)
                
        with session_scope() as db:
            project = project_selector(db, key="ai_recs_project")
            if not project:
                return
            
            recs = _get_cached_recs(project.id)

            st.write("")
            for r in recs:
                impact = r.get("impact", "Medium")
                kind = {"High": "danger", "Medium": "warning", "Low": "info"}.get(impact, "warning")
                with st.container(border=True):
                    st.markdown(f"{status_badge(r.get('category', 'General Advice'), 'info')} &nbsp; {status_badge(impact + ' Impact', kind)}", unsafe_allow_html=True)
                    st.markdown(f"<div style='margin-top:0.4rem;'>{r.get('message', 'The AI generated an incomplete recommendation. Please try again.')}</div>", unsafe_allow_html=True)
                st.write("")

    with tab_delay:
        with session_scope() as db:
            project = project_selector(db, key="ai_delay_project")
            if not project:
                return
            st.write("")
            with st.container(border=True):
                section_header("Delay Risk — What-if Calculator", "Adjust recent attendance and material delays to see the effect on delay risk")
                attendance_rate = st.slider("Recent attendance rate (%)", 0, 100, 90)
                material_delays = st.slider("Materials currently behind delivery", 0, 10, 0)
                risk, level, expected = predict_delay_risk(
                    project.start_date, project.expected_completion, project.progress_percent,
                    attendance_rate_pct=attendance_rate, material_delay_flags=material_delays,
                )
                accent = {"Low": "success", "Moderate": "warning", "High": "danger", "Critical": "danger"}[level]
                st.markdown(status_badge(f"{level} — {risk}/100", accent), unsafe_allow_html=True)
                st.caption(f"Actual progress {project.progress_percent:.0f}% vs. expected {expected:.0f}% at this point in the schedule.")
