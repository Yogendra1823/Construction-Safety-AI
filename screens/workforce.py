from datetime import date

import pandas as pd
import streamlit as st

from database.db import session_scope
from database.models import Worker, Attendance, Expense
from ai_engine.workforce_predictor import suggest_workforce
from config import WORKER_ROLES
from utils.layout import project_selector
from utils.styling import section_header, kpi_card, card_open, card_close


def render():
    section_header("Workforce Management", "Roster, attendance, payroll and AI staffing suggestions")

    with session_scope() as db:
        project = project_selector(db, key="workforce_project")
        if not project:
            return

        workers = db.query(Worker).filter(Worker.project_id == project.id).all()
        today = date.today()
        today_attendance = db.query(Attendance).filter(
            Attendance.project_id == project.id, Attendance.work_date == today
        ).all()
        present_today = sum(1 for a in today_attendance if a.status in ("Present", "Half-day"))
        payroll_today = sum(
            (a.hours_worked / 8) * next((w.daily_wage for w in workers if w.id == a.worker_id), 0)
            for a in today_attendance
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Total Workforce", len(workers), "👷", accent="primary")
        with c2: kpi_card("Present Today", present_today, "✅", accent="success")
        with c3: kpi_card("Absent Today", max(len(workers) - present_today, 0), "❌", accent="warning")
        with c4: kpi_card("Today's Payroll", f"₹{payroll_today:,.0f}", "💵", accent="warning")

        st.write("")
        with st.container(border=True):
            section_header("AI Workforce Suggestion", "Recommended headcount by role for this project's scale")
            suggestion = suggest_workforce(project.plot_size_sqft, project.floors, project.building_type)
            actual_by_role = {}
            for w in workers:
                actual_by_role[w.role] = actual_by_role.get(w.role, 0) + 1
            df_s = pd.DataFrame(suggestion["by_role"])
            df_s["actual_count"] = df_s["role"].map(lambda r: actual_by_role.get(r, 0))
            df_s.columns = ["Role", "AI Suggested", "Currently Assigned"]
            st.dataframe(df_s, use_container_width=True, hide_index=True)

        st.write("")
        with st.container(border=True):
            section_header("Roster & Attendance")
            role_filter = st.selectbox("Filter by role", ["All Roles"] + WORKER_ROLES, key="wf_role_filter")
            filtered = workers if role_filter == "All Roles" else [w for w in workers if w.role == role_filter]

            if filtered:
                att_map = {a.worker_id: a.status for a in today_attendance}
                df = pd.DataFrame([{
                    "Name": w.name, "Role": w.role, "Phone": w.phone, "Daily Wage (₹)": w.daily_wage,
                    "Status": w.status, "Today's Attendance": att_map.get(w.id, "Not marked"),
                } for w in filtered])
                edited = st.data_editor(
                    df, use_container_width=True, hide_index=True, key="workforce_editor",
                    disabled=["Name", "Role", "Phone", "Daily Wage (₹)"],
                    column_config={
                        "Today's Attendance": st.column_config.SelectboxColumn(options=["Not marked", "Present", "Absent", "Half-day"]),
                        "Status": st.column_config.SelectboxColumn(options=["Active", "Inactive"]),
                    },
                )
                if st.button("💾 Save Attendance & Status"):
                    for _, row in edited.iterrows():
                        w = next(w for w in filtered if w.name == row["Name"])
                        w.status = row["Status"]
                        if row["Today's Attendance"] != "Not marked":
                            existing = next((a for a in today_attendance if a.worker_id == w.id), None)
                            hrs = 8 if row["Today's Attendance"] == "Present" else (4 if row["Today's Attendance"] == "Half-day" else 0)
                            
                            if existing:
                                old_hrs = existing.hours_worked
                                existing.status = row["Today's Attendance"]
                                existing.hours_worked = hrs
                                
                                diff_hrs = hrs - old_hrs
                                if diff_hrs != 0:
                                    cost = (abs(diff_hrs) / 8) * w.daily_wage
                                    if diff_hrs > 0:
                                        project.budget_used += cost
                                        db.add(Expense(project_id=project.id, date=today, category="Labor", amount=cost, description=f"Auto-expense: {w.name} attendance update"))
                                    else:
                                        project.budget_used -= cost
                                        db.add(Expense(project_id=project.id, date=today, category="Labor", amount=-cost, description=f"Auto-refund: {w.name} attendance correction"))
                            else:
                                db.add(Attendance(worker_id=w.id, project_id=project.id, work_date=today,
                                                   status=row["Today's Attendance"], hours_worked=hrs))
                                if hrs > 0:
                                    cost = (hrs / 8) * w.daily_wage
                                    project.budget_used += cost
                                    db.add(Expense(project_id=project.id, date=today, category="Labor", amount=cost, description=f"Auto-expense: {w.name} attendance"))
                                    
                    st.success("Saved. Budget and expenses auto-updated.")
                    st.rerun()
            else:
                st.caption("No workers match this filter.")

        st.write("")
        with st.expander("➕ Add a worker to this project"):
            with st.form("add_worker", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                name = c1.text_input("Full name")
                role = c2.selectbox("Role", WORKER_ROLES)
                wage = c3.number_input("Daily wage (₹)", min_value=0.0, value=1200.0)
                phone = st.text_input("Phone")
                if st.form_submit_button("Add Worker"):
                    if name:
                        db.add(Worker(name=name, role=role, daily_wage=wage, phone=phone, status="Active", project_id=project.id))
                        st.rerun()
