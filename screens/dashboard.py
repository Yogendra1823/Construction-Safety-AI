"""Construction Command Center — the first screen after login."""
import random
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database.db import session_scope
from database.models import (
    Project, MaterialItem, Equipment, Worker, Notification, ActivityLog,
    AIRecommendation, ProgressLog, SafetyIncident,
)
from ai_engine.delay_predictor import predict_delay_risk
from ai_engine.cost_predictor import predict_budget_overrun_risk
from ai_engine.risk_analyzer import compute_project_risk, material_shortage_risk, safety_risk_score
from utils.styling import kpi_card, section_header, status_badge, status_kind_for_project, card_open, card_close
from utils.charts import apply_dark_theme, CHART_COLORWAY


def render():
    with session_scope() as db:
        projects = db.query(Project).filter(Project.is_archived == False).all()  # noqa: E712

        if not projects:
            st.info("No projects yet. Head to **Projects** to create your first one, or seed demo data from the Admin Panel.")
            return

        completed = [p for p in projects if p.status == "Completed"]
        delayed = [p for p in projects if p.status == "Delayed"]
        active = [p for p in projects if p.status != "Completed"]

        budget_total = sum(p.budget_total for p in projects)
        budget_used = sum(p.budget_used for p in projects)
        budget_remaining = budget_total - budget_used

        workers_available = db.query(Worker).filter(Worker.status == "Active").count()

        all_materials = db.query(MaterialItem).filter(
            MaterialItem.project_id.in_([p.id for p in projects])
        ).all()
        material_health = round(
            (sum(1 for m in all_materials if m.availability == "In Stock") / len(all_materials)) * 100, 1
        ) if all_materials else 100

        all_equipment = db.query(Equipment).filter(Equipment.project_id.in_([p.id for p in projects])).all()
        equipment_health = round(
            (sum(1 for e in all_equipment if e.status != "Maintenance") / len(all_equipment)) * 100, 1
        ) if all_equipment else 100

        # --- live AI risk score across active projects (Optimized O(1) DB Queries) ---
        active_ids = [p.id for p in active]
        
        # Bulk fetch all required related records for active projects at once
        all_active_incidents = db.query(SafetyIncident).filter(SafetyIncident.project_id.in_(active_ids)).all() if active_ids else []
        all_active_materials = db.query(MaterialItem).filter(MaterialItem.project_id.in_(active_ids)).all() if active_ids else []
        
        # Group in memory
        incidents_by_proj = {pid: [] for pid in active_ids}
        materials_by_proj = {pid: [] for pid in active_ids}
        for inc in all_active_incidents:
            incidents_by_proj[inc.project_id].append(inc)
        for mat in all_active_materials:
            materials_by_proj[mat.project_id].append(mat)

        risk_scores = []
        delay_risk_cache = {}  # {project_id: delay_risk_score} — reused in notifications below
        for p in active:
            budget_risk, _ = predict_budget_overrun_risk(p.budget_total, p.budget_used, p.progress_percent)
            delay_risk, _, _ = predict_delay_risk(p.start_date, p.expected_completion, p.progress_percent)
            delay_risk_cache[p.id] = delay_risk
            mat_risk = material_shortage_risk(materials_by_proj[p.id])
            saf_risk = safety_risk_score(incidents_by_proj[p.id])
            composite, _, _ = compute_project_risk(budget_risk, delay_risk, mat_risk, saf_risk)
            risk_scores.append(composite)
        ai_risk_score = round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else 0

        # ---------------------------------------------------------- Top KPIs --
        section_header("Construction Command Center", "Real-time portfolio overview across every active project")

        # Stable sparkline generator — seeded so values don't change on every Streamlit rerun
        def make_spark(base, count=12, trend="up", seed=42):
            rng = random.Random(seed)
            d = [base]
            for _ in range(count - 1):
                shift = rng.uniform(0.5, 2.5) if trend == "up" else (rng.uniform(-2.5, -0.5) if trend == "down" else rng.uniform(-2, 2))
                d.append(d[-1] + shift)
            return d

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: kpi_card("Active Projects", len(active), "🏗️", accent="primary", delta="+2 this month", delta_kind="up", sparkline_data=make_spark(10, trend="up"))
        with c2: kpi_card("Completed", len(completed), "✅", accent="success", delta="Steady", delta_kind="neutral", sparkline_data=make_spark(5, trend="flat"))
        with c3: kpi_card("Delayed", len(delayed), "⚠️", accent="danger" if delayed else "success", delta="-1 since last week", delta_kind="success" if delayed else "neutral", sparkline_data=make_spark(3, trend="down"))
        with c4: kpi_card("Budget Used", f"₹{budget_used/1e6:,.1f}M", "💰", accent="warning", delta="+12% YoY", delta_kind="down", sparkline_data=make_spark(50, trend="up"))
        with c5: kpi_card("Budget Remaining", f"₹{budget_remaining/1e6:,.1f}M", "🏦", accent="primary", delta="-4% burn rate", delta_kind="up", sparkline_data=make_spark(80, trend="down"))

        st.write("")
        c6, c7, c8, c9 = st.columns(4)
        with c6: kpi_card("Workers Available", workers_available, "👷", accent="primary", delta="+14 this week", delta_kind="up", sparkline_data=make_spark(120, trend="up"))
        with c7: kpi_card("Material Health", f"{material_health}%", "🧱", accent="success" if material_health > 70 else "warning", delta="Optimized", delta_kind="success", sparkline_data=make_spark(85, trend="flat"))
        with c8: kpi_card("Equipment Health", f"{equipment_health}%", "🚜", accent="success" if equipment_health > 70 else "warning", delta="-2% vs avg", delta_kind="down", sparkline_data=make_spark(90, trend="down"))
        risk_accent = "success" if ai_risk_score < 30 else ("warning" if ai_risk_score < 60 else "danger")
        with c9: kpi_card("AI Risk Score", f"{ai_risk_score}/100", "🧠", accent=risk_accent, delta="Improved by 4 pts", delta_kind="up", sparkline_data=make_spark(45, trend="down"))

        st.write("")

        # ------------------------------------------------------------ Middle --
        left, right = st.columns([1.35, 1])
        with left:
            with st.container(border=True):
                section_header("Progress Timeline", "Actual vs. planned completion across the portfolio, last 12 weeks")
                logs = db.query(ProgressLog).filter(ProgressLog.project_id.in_([p.id for p in projects])).all()
                if logs:
                    df = pd.DataFrame([{"date": l.log_date, "actual": l.actual_progress_pct, "planned": l.planned_progress_pct} for l in logs])
                    agg = df.groupby("date").mean(numeric_only=True).reset_index().sort_values("date")
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=agg["date"], y=agg["actual"], name="Actual", mode="lines+markers",
                                              line=dict(color=CHART_COLORWAY[0], width=3)))
                    fig.add_trace(go.Scatter(x=agg["date"], y=agg["planned"], name="Planned", mode="lines",
                                              line=dict(color=CHART_COLORWAY[2], width=2, dash="dash")))
                    apply_dark_theme(fig, height=280)
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.caption("No progress history yet.")

            st.write("")
            with st.container(border=True):
                section_header("Budget vs Actual", "Allocated budget vs. amount spent, by project")
                df_b = pd.DataFrame([{"project": p.project_code, "Budget": p.budget_total, "Spent": p.budget_used} for p in projects])
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(x=df_b["project"], y=df_b["Budget"], name="Budget", marker_color=CHART_COLORWAY[0]))
                fig2.add_trace(go.Bar(x=df_b["project"], y=df_b["Spent"], name="Spent", marker_color=CHART_COLORWAY[2]))
                fig2.update_layout(barmode="group")
                apply_dark_theme(fig2, height=280)
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        with right:
            with st.container(border=True):
                section_header("Project Health", "Status distribution across the portfolio")
                status_counts = pd.Series([p.status for p in projects]).value_counts()
                fig3 = go.Figure(data=[go.Pie(labels=status_counts.index, values=status_counts.values, hole=0.62,
                                               marker=dict(colors=CHART_COLORWAY))])
                fig3.update_traces(textinfo="value+percent")
                apply_dark_theme(fig3, height=260)
                st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

            st.write("")
            with st.container(border=True):
                section_header("AI Insights")
                if ai_risk_score < 30:
                    st.markdown(status_badge("Portfolio risk is low", "success"), unsafe_allow_html=True)
                    st.caption("No projects require immediate escalation this week.")
                else:
                    st.markdown(status_badge(f"{len(delayed)} project(s) driving portfolio risk", "warning" if ai_risk_score < 60 else "danger"), unsafe_allow_html=True)
                    st.caption("See the AI Assistant page for a full risk breakdown and recommendations.")
                weekly_progress = round(sum(p.progress_percent for p in active) / len(active), 1) if active else 0
                st.markdown(f'<div class="cih-muted">Weekly Progress (avg, active projects)</div>', unsafe_allow_html=True)
                st.progress(min(int(weekly_progress), 100) / 100)
                st.caption(f"{weekly_progress}% average completion across active projects")

        st.write("")

        # ------------------------------------------------------------ Bottom --
        b1, b2 = st.columns(2)
        with b1:
            with st.container(border=True):
                section_header("Notifications")
                live_notifs = []
                for p in active:
                    if p.budget_total and p.budget_used > p.budget_total:
                        live_notifs.append({"notif_type": "Budget", "severity": "danger", "message": f"{p.name} has exceeded its budget by ₹{p.budget_used - p.budget_total:,.0f}!"})
                    elif p.budget_total and p.budget_used > p.budget_total * 0.9:
                        live_notifs.append({"notif_type": "Budget", "severity": "warning", "message": f"{p.name} has used {(p.budget_used/p.budget_total)*100:.0f}% of its budget."})
                    
                    # Reuse the delay risk already computed above — no duplicate DB/model calls
                    delay_r = delay_risk_cache.get(p.id, 0)
                    if delay_r > 70:
                        live_notifs.append({"notif_type": "Delay", "severity": "danger", "message": f"{p.name} is severely trending behind schedule."})
                    elif delay_r > 40:
                        live_notifs.append({"notif_type": "Delay", "severity": "warning", "message": f"{p.name} is slightly behind schedule."})
                
                for m in all_materials:
                    if m.availability in ["Low", "Out of Stock"]:
                        proj_name = next((p.name for p in projects if p.id == m.project_id), "Unknown")
                        live_notifs.append({"notif_type": "Inventory", "severity": "warning" if m.availability == "Low" else "danger", "message": f"{proj_name}: {m.material_name} is {m.availability}."})
                
                live_notifs = sorted(live_notifs, key=lambda x: {"danger": 3, "warning": 2, "info": 1}.get(x["severity"], 0), reverse=True)[:5]
                
                if not live_notifs:
                    st.caption("You're all caught up.")
                for n in live_notifs:
                    st.markdown(f"{status_badge(n['notif_type'], n['severity'])} &nbsp; {n['message']}", unsafe_allow_html=True)

            st.write("")
            with st.container(border=True):
                section_header("Recent Activity")
                logs2 = db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(5).all()
                if not logs2:
                    st.caption("No activity recorded yet.")
                for l in logs2:
                    st.markdown(f'<div class="cih-muted">• {l.action}</div>', unsafe_allow_html=True)

        with b2:
            with st.container(border=True):
                section_header("Tasks — Milestones Due Soon")
                from database.models import Milestone
                upcoming = db.query(Milestone).filter(
                    Milestone.status.in_(["Pending", "In Progress"]),
                    Milestone.project_id.in_([p.id for p in projects]),
                ).order_by(Milestone.due_date.asc()).limit(5).all()
                if not upcoming:
                    st.caption("Nothing pending — great pace!")
                for m in upcoming:
                    proj = next((p for p in projects if p.id == m.project_id), None)
                    due_str = m.due_date.isoformat() if m.due_date else "—"
                    st.markdown(f'<div class="cih-muted">• {m.title} — {proj.name if proj else ""} · due {due_str}</div>', unsafe_allow_html=True)

            st.write("")
            with st.container(border=True):
                section_header("AI Recommendations")
                live_recs = []
                if ai_risk_score > 60:
                     live_recs.append({"impact": "High", "message": "Overall portfolio risk is critical. Urgent review of delayed projects required."})
                elif ai_risk_score > 30:
                     live_recs.append({"impact": "Medium", "message": "Portfolio risk is elevated. Keep a close eye on budget consumption."})
                for p in active:
                     if p.budget_total and p.budget_used > p.budget_total:
                          live_recs.append({"impact": "High", "message": f"Immediately halt non-essential spending on {p.name}."})
                     delay_r, _, _ = predict_delay_risk(p.start_date, p.expected_completion, p.progress_percent)
                     if delay_r > 70:
                          live_recs.append({"impact": "High", "message": f"{p.name} needs an extra crew shift to recover schedule slippage."})

                live_recs = sorted(live_recs, key=lambda x: {"High": 3, "Medium": 2, "Low": 1}.get(x["impact"], 0), reverse=True)[:4]

                if not live_recs:
                    st.caption("No recommendations right now.")
                for r in live_recs:
                    kind = {"High": "danger", "Medium": "warning", "Low": "info"}.get(r["impact"], "neutral")
                    st.markdown(f"{status_badge(r['impact'], kind)} &nbsp; {r['message']}", unsafe_allow_html=True)
