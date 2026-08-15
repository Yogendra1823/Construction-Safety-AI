from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database.db import session_scope
from database.models import BudgetItem, Expense
from ai_engine.cost_predictor import predict_budget_overrun_risk
from utils.layout import project_selector
from utils.styling import section_header, kpi_card, status_badge, card_open, card_close
from utils.charts import apply_dark_theme, CHART_COLORWAY


def render():
    section_header("Budget Management", "Track allocation, spend, and forecast for every project")

    with session_scope() as db:
        project = project_selector(db, key="budget_project")
        if not project:
            return

        budget_items = db.query(BudgetItem).filter(BudgetItem.project_id == project.id).all()
        expenses = db.query(Expense).filter(Expense.project_id == project.id).order_by(Expense.expense_date).all()

        remaining = project.budget_total - project.budget_used
        risk_pct, risk_level = predict_budget_overrun_risk(project.budget_total, project.budget_used, project.progress_percent)
        forecast_final = project.budget_total * (1 + risk_pct / 200)  # mild forecast nudge based on overrun risk

        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Total Budget", f"₹{project.budget_total:,.0f}", "💰", accent="primary")
        with c2: kpi_card("Spent", f"₹{project.budget_used:,.0f}", "📤", accent="warning")
        with c3: kpi_card("Remaining", f"₹{remaining:,.0f}", "🏦", accent="success" if remaining >= 0 else "danger")
        accent = {"Low": "success", "Moderate": "warning", "High": "danger", "Critical": "danger"}[risk_level]
        with c4: kpi_card("Overrun Risk", f"{risk_level} ({risk_pct}%)", "🧠", accent=accent)

        st.write("")
        left, right = st.columns([1.3, 1])
        with left:
            with st.container(border=True):
                section_header("Cost Trends", "Cumulative spend over time")
                if expenses:
                    df = pd.DataFrame([{"date": e.expense_date, "amount": e.amount} for e in expenses])
                    df = df.groupby("date").sum().reset_index().sort_values("date")
                    df["cumulative"] = df["amount"].cumsum()
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df["date"], y=df["cumulative"], fill="tozeroy",
                                              line=dict(color=CHART_COLORWAY[0], width=3)))
                    apply_dark_theme(fig, height=280, show_legend=False)
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.caption("No expenses logged yet.")

        with right:
            with st.container(border=True):
                section_header("Budget Allocation", "By category")
                if budget_items:
                    fig2 = go.Figure(data=[go.Pie(
                        labels=[b.category for b in budget_items],
                        values=[b.allocated_amount for b in budget_items],
                        hole=0.55, marker=dict(colors=CHART_COLORWAY),
                    )])
                    apply_dark_theme(fig2, height=260)
                    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.caption("No budget categories set up yet.")

        st.write("")
        with st.container(border=True):
            section_header("Budget by Category", "Allocated vs. spent")
            if budget_items:
                df_b = pd.DataFrame([{
                    "Category": b.category, "Allocated (₹)": b.allocated_amount, "Spent (₹)": b.spent_amount,
                    "Utilization %": round((b.spent_amount / b.allocated_amount) * 100, 1) if b.allocated_amount else 0,
                } for b in budget_items])
                st.dataframe(df_b, use_container_width=True, hide_index=True)
            with st.form("add_budget_cat", clear_on_submit=True):
                c1, c2 = st.columns(2)
                cat = c1.text_input("Category name")
                alloc = c2.number_input("Allocated amount (₹)", min_value=0.0, value=100000.0)
                if st.form_submit_button("Add / Update Category"):
                    if cat:
                        existing = next((b for b in budget_items if b.category.lower() == cat.lower()), None)
                        if existing:
                            existing.allocated_amount = alloc
                        else:
                            db.add(BudgetItem(project_id=project.id, category=cat, allocated_amount=alloc, spent_amount=0))
                        st.rerun()

        st.write("")
        with st.container(border=True):
            section_header("Expenses")
            if expenses:
                df_e = pd.DataFrame([{"Date": e.expense_date, "Category": e.category, "Description": e.description, "Amount (₹)": e.amount} for e in expenses])
                st.dataframe(df_e.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
            with st.form("add_expense", clear_on_submit=True):
                c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
                cat = c1.selectbox("Category", [b.category for b in budget_items] or ["Materials", "Labor", "Equipment", "Overhead"])
                amt = c2.number_input("Amount (₹)", min_value=0.0, value=10000.0)
                desc = c3.text_input("Description")
                edate = c4.date_input("Date", value=date.today())
                if st.form_submit_button("Log Expense", type="primary"):
                    db.add(Expense(project_id=project.id, category=cat, description=desc, amount=amt, expense_date=edate))
                    project.budget_used += amt
                    bi = next((b for b in budget_items if b.category == cat), None)
                    if bi:
                        bi.spent_amount += amt
                    st.success("Expense logged.")
                    st.rerun()
