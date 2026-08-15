import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database.db import session_scope
from database.models import MaterialItem
from utils.layout import project_selector
from utils.styling import section_header, kpi_card, card_open, card_close
from utils.charts import apply_dark_theme, CHART_COLORWAY
from utils.pdf_export import generate_boq_pdf
from utils.excel_export import generate_boq_excel


def render():
    section_header("BOQ Generator", "Automatically generate a Bill of Quantities from a project's material estimate")

    with session_scope() as db:
        project = project_selector(db, key="boq_project")
        if not project:
            return

        materials = db.query(MaterialItem).filter(MaterialItem.project_id == project.id).all()
        if not materials:
            st.warning("This project has no material estimate yet — add materials from the Materials page first.")
            return

        grand_total = sum(m.total_cost for m in materials)
        c1, c2, c3 = st.columns(3)
        with c1: kpi_card("Line Items", len(materials), "🧾", accent="primary")
        with c2: kpi_card("Grand Total", f"₹{grand_total:,.0f}", "💰", accent="warning")
        with c3: kpi_card("Structural Share", f"{sum(m.total_cost for m in materials if m.category=='Structural')/grand_total*100:.0f}%", "🏗️", accent="primary")

        st.write("")
        left, right = st.columns([1.4, 1])
        with left:
            with st.container(border=True):
                section_header("Bill of Quantities")
                df = pd.DataFrame([{
                    "Material": m.material_name, "Category": m.category, "Unit": m.unit,
                    "Est. Qty": m.estimated_qty, "Unit Cost (₹)": m.unit_cost, "Total Cost (₹)": m.total_cost,
                } for m in materials])
                st.dataframe(df, use_container_width=True, hide_index=True)

        with right:
            with st.container(border=True):
                section_header("Cost Breakdown", "By category")
                cat_totals = {}
                for m in materials:
                    cat_totals[m.category] = cat_totals.get(m.category, 0) + m.total_cost
                fig = go.Figure(data=[go.Pie(labels=list(cat_totals.keys()), values=list(cat_totals.values()),
                                              hole=0.55, marker=dict(colors=CHART_COLORWAY))])
                apply_dark_theme(fig, height=260)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.write("")
        pdf_bytes = generate_boq_pdf(project, materials)
        xlsx_bytes = generate_boq_excel(project, materials)
        d1, d2 = st.columns(2)
        with d1:
            st.download_button("⬇️ Download BOQ as PDF", data=pdf_bytes,
                                file_name=f"BOQ_{project.project_code}.pdf", mime="application/pdf",
                                use_container_width=True)
        with d2:
            st.download_button("⬇️ Download BOQ as Excel", data=xlsx_bytes,
                                file_name=f"BOQ_{project.project_code}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True)
