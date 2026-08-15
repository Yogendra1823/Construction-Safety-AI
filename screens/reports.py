from datetime import date

import streamlit as st

from database.db import session_scope
from database.models import Project, MaterialItem, BudgetItem, Worker, Attendance, InventoryItem, Expense
from ai_engine.risk_analyzer import compute_project_risk, material_shortage_risk, safety_risk_score
from ai_engine.cost_predictor import predict_budget_overrun_risk
from ai_engine.delay_predictor import predict_delay_risk
from database.models import SafetyIncident
from utils.layout import project_selector
from utils.styling import section_header, card_open, card_close
from utils.pdf_export import generate_project_report_pdf
from utils.excel_export import generate_report_excel

REPORT_TYPES = ["Project Report", "Budget Report", "Worker Report", "Inventory Report", "AI Summary Report"]


def _project_report_sections(db, project):
    milestones_rows = [["Milestone", "Due", "Status"]]
    from database.models import Milestone
    for m in db.query(Milestone).filter(Milestone.project_id == project.id).all():
        milestones_rows.append([m.title, str(m.due_date or "-"), m.status])

    overview_rows = [
        ["Field", "Value"],
        ["Client", project.client_name or "-"],
        ["Location", project.location or "-"],
        ["Building Type", project.building_type or "-"],
        ["Status", project.status],
        ["Progress", f"{project.progress_percent:.0f}%"],
        ["Budget Total", f"₹{project.budget_total:,.0f}"],
        ["Budget Used", f"₹{project.budget_used:,.0f}"],
    ]
    return {"Overview": overview_rows, "Milestones": milestones_rows}


def _budget_report_sections(db, project):
    budget_items = db.query(BudgetItem).filter(BudgetItem.project_id == project.id).all()
    rows = [["Category", "Allocated (₹)", "Spent (₹)"]]
    for b in budget_items:
        rows.append([b.category, f"{b.allocated_amount:,.0f}", f"{b.spent_amount:,.0f}"])

    expenses = db.query(Expense).filter(Expense.project_id == project.id).order_by(Expense.expense_date.desc()).limit(20).all()
    exp_rows = [["Date", "Category", "Description", "Amount (₹)"]]
    for e in expenses:
        exp_rows.append([str(e.expense_date), e.category, e.description or "-", f"{e.amount:,.0f}"])
    return {"Budget by Category": rows, "Recent Expenses": exp_rows}


def _worker_report_sections(db, project):
    workers = db.query(Worker).filter(Worker.project_id == project.id).all()
    rows = [["Name", "Role", "Daily Wage (₹)", "Status"]]
    for w in workers:
        rows.append([w.name, w.role, f"{w.daily_wage:,.0f}", w.status])
    return {"Workforce Roster": rows}


def _inventory_report_sections(db):
    items = db.query(InventoryItem).all()
    rows = [["Item", "Category", "In Stock", "Unit", "Reorder Level"]]
    for i in items:
        rows.append([i.item_name, i.category, f"{i.quantity_in_stock:,.0f}", i.unit, f"{i.reorder_level:,.0f}"])
    return {"Warehouse Inventory": rows}


def _ai_summary_sections(db, project):
    materials = db.query(MaterialItem).filter(MaterialItem.project_id == project.id).all()
    incidents = db.query(SafetyIncident).filter(SafetyIncident.project_id == project.id).all()
    budget_risk, _ = predict_budget_overrun_risk(project.budget_total, project.budget_used, project.progress_percent)
    delay_risk, delay_level, expected = predict_delay_risk(project.start_date, project.expected_completion, project.progress_percent)
    mat_risk = material_shortage_risk(materials)
    saf_risk = safety_risk_score(incidents)
    composite, level, breakdown = compute_project_risk(budget_risk, delay_risk, mat_risk, saf_risk)

    rows = [
        ["Metric", "Value"],
        ["Composite AI Risk Score", f"{composite}/100 ({level})"],
        ["Budget Overrun Risk", f"{breakdown['budget_risk']}/100"],
        ["Delay Risk", f"{breakdown['delay_risk']}/100 ({delay_level})"],
        ["Material Shortage Risk", f"{breakdown['material_risk']}/100"],
        ["Safety Risk", f"{breakdown['safety_risk']}/100"],
        ["Progress vs Schedule", f"{project.progress_percent:.0f}% actual vs {expected:.0f}% expected"],
    ]
    return {"AI Risk Summary": rows}


def render():
    section_header("Reports", "Generate and export reports as PDF or Excel")

    report_type = st.selectbox("Report type", REPORT_TYPES)

    with session_scope() as db:
        project = None
        if report_type != "Inventory Report":
            project = project_selector(db, key="reports_project")
            if not project:
                return

        if report_type == "Project Report":
            sections = _project_report_sections(db, project)
        elif report_type == "Budget Report":
            sections = _budget_report_sections(db, project)
        elif report_type == "Worker Report":
            sections = _worker_report_sections(db, project)
        elif report_type == "Inventory Report":
            sections = _inventory_report_sections(db)
        else:
            sections = _ai_summary_sections(db, project)

        st.write("")
        with st.container(border=True):
            section_header(report_type, "Preview")
            for title, rows in sections.items():
                st.markdown(f"**{title}**")
                if len(rows) > 1:
                    import pandas as pd
                    st.dataframe(pd.DataFrame(rows[1:], columns=rows[0]), use_container_width=True, hide_index=True)
                else:
                    st.caption("No data.")

        st.write("")
        pdf_ref = project if project else type("obj", (), {"name": "Inventory", "project_code": "GLOBAL"})
        pdf_bytes = generate_project_report_pdf(pdf_ref, sections)
        excel_sheets = {title: (rows[0], rows[1:]) for title, rows in sections.items()}
        xlsx_bytes = generate_report_excel(excel_sheets)

        d1, d2 = st.columns(2)
        fname_base = f"{report_type.replace(' ', '_')}_{project.project_code if project else 'ALL'}_{date.today().isoformat()}"
        with d1:
            st.download_button("⬇️ Download as PDF", data=pdf_bytes, file_name=f"{fname_base}.pdf",
                                mime="application/pdf", use_container_width=True)
        with d2:
            st.download_button("⬇️ Download as Excel", data=xlsx_bytes, file_name=f"{fname_base}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True)
