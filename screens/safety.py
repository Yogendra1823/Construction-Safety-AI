from datetime import date

import pandas as pd
import streamlit as st

from database.db import session_scope
from database.models import SafetyChecklistItem, SafetyIncident, EmergencyContact
from ai_engine.risk_analyzer import safety_risk_score
from utils.layout import project_selector
from utils.styling import section_header, kpi_card, status_badge, card_open, card_close


def render():
    section_header("Safety", "PPE checklist, incident log, risk alerts and emergency contacts")

    with session_scope() as db:
        project = project_selector(db, key="safety_project")
        if not project:
            return

        checklist = db.query(SafetyChecklistItem).filter(SafetyChecklistItem.project_id == project.id).all()
        incidents = db.query(SafetyIncident).filter(SafetyIncident.project_id == project.id).order_by(SafetyIncident.incident_date.desc()).all()
        open_incidents = [i for i in incidents if i.status == "Open"]
        pass_rate = round((sum(1 for c in checklist if c.status == "Pass") / len(checklist)) * 100, 1) if checklist else 100
        risk_score = safety_risk_score(incidents)

        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Open Incidents", len(open_incidents), "🚨", accent="danger" if open_incidents else "success")
        with c2: kpi_card("Checklist Pass Rate", f"{pass_rate}%", "✅", accent="success" if pass_rate > 85 else "warning")
        with c3: kpi_card("Total Incidents Logged", len(incidents), "📋", accent="primary")
        with c4: kpi_card("Safety Risk Score", f"{risk_score}/100", "🧠", accent="danger" if risk_score > 40 else "success")

        st.write("")
        with st.container(border=True):
            section_header("PPE & Site Inspection Checklist")
            if checklist:
                df = pd.DataFrame([{"Item": c.item_name, "Category": c.category, "Status": c.status, "Checked": c.checked_date} for c in checklist])
                edited = st.data_editor(df, use_container_width=True, hide_index=True, key="checklist_editor",
                                         disabled=["Item", "Category", "Checked"],
                                         column_config={"Status": st.column_config.SelectboxColumn(options=["Pass", "Fail", "Pending"])})
                if st.button("💾 Save Checklist"):
                    for _, row in edited.iterrows():
                        item = next(c for c in checklist if c.item_name == row["Item"])
                        item.status = row["Status"]
                        item.checked_date = date.today()
                    st.rerun()
            with st.form("add_checklist", clear_on_submit=True):
                c1, c2 = st.columns(2)
                name = c1.text_input("Checklist item")
                cat = c2.selectbox("Category", ["PPE", "Site", "Equipment"])
                if st.form_submit_button("Add Item"):
                    if name:
                        db.add(SafetyChecklistItem(project_id=project.id, item_name=name, category=cat, status="Pending"))
                        st.rerun()

        st.write("")
        with st.container(border=True):
            section_header("Incident Log")
            if incidents:
                df_i = pd.DataFrame([{"Date": i.incident_date, "Type": i.incident_type, "Severity": i.severity, "Status": i.status, "Description": i.description} for i in incidents])
                st.dataframe(df_i, use_container_width=True, hide_index=True)
            with st.form("add_incident", clear_on_submit=True):
                c1, c2 = st.columns(2)
                itype = c1.text_input("Incident type")
                severity = c2.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
                desc = st.text_area("Description")
                if st.form_submit_button("Log Incident", type="primary"):
                    if itype:
                        db.add(SafetyIncident(project_id=project.id, incident_type=itype, severity=severity,
                                               description=desc, incident_date=date.today(), status="Open"))
                        st.rerun()

        st.write("")
        with st.container(border=True):
            section_header("Emergency Contacts")
            contacts = db.query(EmergencyContact).all()
            for c in contacts:
                st.markdown(f"**{c.name}** — {c.role} &nbsp;·&nbsp; {status_badge(c.contact_type, 'info')} &nbsp;·&nbsp; 📞 {c.phone}", unsafe_allow_html=True)
