import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database.db import session_scope
from database.models import Project, Worker, ProgressLog
from utils.styling import section_header, kpi_card, card_open, card_close
from utils.charts import apply_dark_theme, CHART_COLORWAY


def render():
    section_header("Analytics", "Portfolio-wide trends and comparisons across every project")

    with session_scope() as db:
        projects = db.query(Project).filter(Project.is_archived == False).all()  # noqa: E712
        if not projects:
            st.info("No projects yet.")
            return

        workers = db.query(Worker).count()
        total_budget = sum(p.budget_total for p in projects)
        avg_cost = total_budget / len(projects)
        completed = sum(1 for p in projects if p.status == "Completed")
        ongoing = sum(1 for p in projects if p.status == "Ongoing")
        delayed = sum(1 for p in projects if p.status == "Delayed")

        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Total Projects", len(projects), "🏗️", accent="primary")
        with c2: kpi_card("Total Workers", workers, "👷", accent="primary")
        with c3: kpi_card("Total Budget", f"₹{total_budget/1e6:,.1f}M", "💰", accent="warning")
        with c4: kpi_card("Average Project Cost", f"₹{avg_cost/1e6:,.2f}M", "📐", accent="primary")

        st.write("")
        c5, c6, c7 = st.columns(3)
        with c5: kpi_card("Completed", completed, "✅", accent="success")
        with c6: kpi_card("Ongoing", ongoing, "⚙️", accent="primary")
        with c7: kpi_card("Delayed", delayed, "⚠️", accent="danger" if delayed else "success")

        st.write("")
        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                section_header("Project Status", "Distribution across the portfolio")
                status_counts = pd.Series([p.status for p in projects]).value_counts()
                fig = go.Figure(data=[go.Bar(x=status_counts.index, y=status_counts.values, marker_color=CHART_COLORWAY[0])])
                apply_dark_theme(fig, height=280, show_legend=False)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with right:
            with st.container(border=True):
                section_header("Project Cost Comparison")
                fig2 = go.Figure(data=[go.Bar(
                    x=[p.project_code for p in projects], y=[p.budget_total for p in projects],
                    marker_color=CHART_COLORWAY[2],
                )])
                apply_dark_theme(fig2, height=280, show_legend=False)
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        st.write("")
        with st.container(border=True):
            section_header("Progress Trend", "Portfolio-average actual vs. planned completion")
            logs = db.query(ProgressLog).filter(ProgressLog.project_id.in_([p.id for p in projects])).all()
            if logs:
                df = pd.DataFrame([{"date": l.log_date, "actual": l.actual_progress_pct, "planned": l.planned_progress_pct} for l in logs])
                agg = df.groupby("date").mean(numeric_only=True).reset_index().sort_values("date")
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(x=agg["date"], y=agg["actual"], name="Actual", line=dict(color=CHART_COLORWAY[0], width=3)))
                fig3.add_trace(go.Scatter(x=agg["date"], y=agg["planned"], name="Planned", line=dict(color=CHART_COLORWAY[2], width=2, dash="dash")))
                apply_dark_theme(fig3, height=280)
                st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
            else:
                st.caption("No progress history yet.")

        st.write("")
        with st.container(border=True):
            section_header("Building Type Comparison", "Average budget by building type")
            df_bt = pd.DataFrame([{"type": p.building_type, "budget": p.budget_total} for p in projects])
            avg_by_type = df_bt.groupby("type").mean(numeric_only=True).reset_index()
            fig4 = go.Figure(data=[go.Bar(x=avg_by_type["type"], y=avg_by_type["budget"], marker_color=CHART_COLORWAY[4])])
            apply_dark_theme(fig4, height=260, show_legend=False)
            st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
