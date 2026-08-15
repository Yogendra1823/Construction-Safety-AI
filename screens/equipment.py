from datetime import date

import pandas as pd
import streamlit as st

from database.db import session_scope
from database.models import Equipment, Project
from config import EQUIPMENT_TYPES
from utils.styling import section_header, kpi_card, status_badge, card_open, card_close


def render():
    section_header("Equipment", "Fleet tracking — cranes, mixers, trucks, excavators and more")

    with session_scope() as db:
        projects = {p.id: p for p in db.query(Project).filter(Project.is_archived == False).all()}  # noqa: E712
        equipment = db.query(Equipment).all()

        available = sum(1 for e in equipment if e.status == "Available")
        in_use = sum(1 for e in equipment if e.status == "In Use")
        maintenance = sum(1 for e in equipment if e.status == "Maintenance")
        avg_fuel = round(sum(e.fuel_level for e in equipment) / len(equipment), 1) if equipment else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Total Fleet", len(equipment), "🚜", accent="primary")
        with c2: kpi_card("Available", available, "✅", accent="success")
        with c3: kpi_card("In Use", in_use, "⚙️", accent="warning")
        with c4: kpi_card("In Maintenance", maintenance, "🛠️", accent="danger" if maintenance else "success")

        st.write("")
        with st.container(border=True):
            section_header("Fleet Status")
            type_filter = st.selectbox("Filter by type", ["All Types"] + EQUIPMENT_TYPES, key="eq_type_filter")
            filtered = equipment if type_filter == "All Types" else [e for e in equipment if e.equipment_type == type_filter]

            if filtered:
                rows = []
                for e in filtered:
                    proj = projects.get(e.project_id)
                    rows.append({
                        "Equipment": e.name, "Type": e.equipment_type, "Project": proj.name if proj else "Unassigned",
                        "Status": e.status, "Fuel %": e.fuel_level, "Usage Hrs": e.usage_hours,
                        "Last Maintenance": e.last_maintenance, "Next Maintenance": e.next_maintenance,
                    })
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True)

                overdue = [e for e in filtered if e.next_maintenance and e.next_maintenance <= date.today()]
                if overdue:
                    st.markdown(status_badge(f"{len(overdue)} unit(s) overdue for maintenance", "danger"), unsafe_allow_html=True)
            else:
                st.caption("No equipment matches this filter.")

        st.write("")
        with st.expander("➕ Add equipment"):
            with st.form("add_equipment", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                name = c1.text_input("Equipment name")
                etype = c2.selectbox("Type", EQUIPMENT_TYPES)
                proj_choice = c3.selectbox("Assign to project", ["Unassigned"] + [p.name for p in projects.values()])
                c4, c5 = st.columns(2)
                fuel = c4.number_input("Fuel level %", 0, 100, 100)
                status = c5.selectbox("Status", ["Available", "In Use", "Maintenance"])
                if st.form_submit_button("Add Equipment"):
                    if name:
                        proj_id = next((pid for pid, p in projects.items() if p.name == proj_choice), None)
                        db.add(Equipment(name=name, equipment_type=etype, project_id=proj_id,
                                          status=status, fuel_level=fuel, usage_hours=0))
                        st.rerun()
