import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database.db import session_scope
from database.models import MaterialItem, Expense
from utils.layout import project_selector
from utils.styling import section_header, kpi_card, card_open, card_close
from utils.charts import apply_dark_theme, CHART_COLORWAY


def render():
    section_header("Materials", "Track estimated vs. used quantities and supplier availability by project")

    with session_scope() as db:
        project = project_selector(db, key="materials_project")
        if not project:
            return

        materials = db.query(MaterialItem).filter(MaterialItem.project_id == project.id).all()
        if not materials:
            st.info("No materials estimated for this project yet. Use the AI Assistant → Material Estimation to generate them, or add manually below.")

        total_cost = sum(m.total_cost for m in materials)
        avg_usage = round(sum(m.usage_pct for m in materials) / len(materials), 1) if materials else 0
        low_stock = sum(1 for m in materials if m.availability in ("Low", "Out of Stock"))

        c1, c2, c3 = st.columns(3)
        with c1: kpi_card("Total Material Cost", f"₹{total_cost:,.0f}", "💰", accent="primary")
        with c2: kpi_card("Avg. Usage", f"{avg_usage}%", "📈", accent="warning" if avg_usage > 80 else "success")
        with c3: kpi_card("Low / Out of Stock Items", low_stock, "⚠️", accent="danger" if low_stock else "success")

        st.write("")
        if materials:
            with st.container(border=True):
                section_header("Usage by Material")
                df_chart = pd.DataFrame([{"material": m.material_name, "estimated": m.estimated_qty, "used": m.used_qty} for m in materials])
                fig = go.Figure()
                fig.add_trace(go.Bar(x=df_chart["material"], y=df_chart["estimated"], name="Estimated", marker_color=CHART_COLORWAY[0]))
                fig.add_trace(go.Bar(x=df_chart["material"], y=df_chart["used"], name="Used", marker_color=CHART_COLORWAY[2]))
                fig.update_layout(barmode="overlay")
                apply_dark_theme(fig, height=300)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.write("")
        with st.container(border=True):
            section_header("Material Breakdown")
            categories = ["All Categories"] + sorted({m.category for m in materials})
            cat_filter = st.selectbox("Filter by category", categories, key="mat_cat_filter") if materials else "All Categories"
            filtered = materials if cat_filter == "All Categories" else [m for m in materials if m.category == cat_filter]

            if filtered:
                df = pd.DataFrame([{
                    "Material": m.material_name, "Unit": m.unit, "Estimated": m.estimated_qty,
                    "Used": m.used_qty, "Remaining": m.remaining_qty, "Usage %": m.usage_pct,
                    "Unit Cost (₹)": m.unit_cost, "Total Cost (₹)": m.total_cost,
                    "Supplier": m.supplier, "Availability": m.availability,
                } for m in filtered])

                edited = st.data_editor(
                    df, use_container_width=True, hide_index=True, key="materials_editor",
                    disabled=["Material", "Unit", "Estimated", "Remaining", "Usage %", "Unit Cost (₹)", "Total Cost (₹)"],
                    column_config={
                        "Availability": st.column_config.SelectboxColumn(options=["In Stock", "Low", "Out of Stock"]),
                    },
                )
                if st.button("💾 Save Changes", key="save_materials"):
                    for _, row in edited.iterrows():
                        m = next(m for m in filtered if m.material_name == row["Material"])
                        
                        old_used = m.used_qty
                        new_used = float(row["Used"])
                        
                        if new_used > old_used:
                            diff = new_used - old_used
                            cost = diff * m.unit_cost
                            
                            # Auto-update project budget
                            project.budget_used += cost
                            
                            # Auto-generate expense record
                            db.add(Expense(
                                project_id=project.id,
                                date=pd.Timestamp.today().date(),
                                category="Materials",
                                amount=cost,
                                description=f"Auto-expense: {diff} {m.unit} of {m.material_name} consumed."
                            ))
                            
                        m.used_qty = new_used
                        m.supplier = row["Supplier"]
                        m.availability = row["Availability"]
                        
                    st.success("Materials updated. Budget and expenses auto-updated.")
                    st.rerun()

        st.write("")
        with st.expander("➕ Add a material manually"):
            with st.form("add_material", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                name = c1.text_input("Material name")
                unit = c2.text_input("Unit", value="units")
                category = c3.selectbox("Category", ["Structural", "Finishing"])
                c4, c5 = st.columns(2)
                qty = c4.number_input("Estimated Quantity", min_value=0.0, value=100.0)
                cost = c5.number_input("Unit Cost (₹)", min_value=0.0, value=100.0)
                if st.form_submit_button("Add Material"):
                    if name:
                        db.add(MaterialItem(project_id=project.id, material_name=name, category=category,
                                             unit=unit, estimated_qty=qty, used_qty=0, unit_cost=cost,
                                             supplier="TBD", availability="In Stock"))
                        st.rerun()
