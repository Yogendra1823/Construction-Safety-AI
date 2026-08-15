import pandas as pd
import streamlit as st

from database.db import session_scope
from database.models import Document, Project
from auth.auth_utils import current_user
from utils.styling import section_header, kpi_card, card_open, card_close


def render():
    section_header("Documents", "Every file across every project, in one library")

    with session_scope() as db:
        docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
        projects = {p.id: p for p in db.query(Project).all()}

        total_size_mb = sum(d.size_kb for d in docs) / 1024
        c1, c2 = st.columns(2)
        with c1: kpi_card("Total Documents", len(docs), "🗂️", accent="primary")
        with c2: kpi_card("Total Storage Used", f"{total_size_mb:,.1f} MB", "💾", accent="primary")

        st.write("")
        search = st.text_input("🔍 Search documents", placeholder="Search by name or project...")
        filtered = docs
        if search:
            s = search.lower()
            filtered = [d for d in docs if s in d.name.lower() or s in (projects.get(d.project_id).name.lower() if d.project_id in projects else "")]

        with st.container(border=True):
            if filtered:
                df = pd.DataFrame([{
                    "Document": d.name, "Project": projects.get(d.project_id).name if d.project_id in projects else "—",
                    "Category": d.category, "Size (KB)": d.size_kb, "Status": d.status, "Uploaded": d.uploaded_at.date(),
                } for d in filtered])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.caption("No documents found.")

        st.write("")
        with st.expander("➕ Upload a document"):
            proj_choice = st.selectbox("Project", [p.name for p in projects.values()])
            uploaded = st.file_uploader("Choose a file")
            if uploaded is not None and st.button("Save to library"):
                proj_id = next(pid for pid, p in projects.items() if p.name == proj_choice)
                db.add(Document(project_id=proj_id, name=uploaded.name, category=uploaded.name.split(".")[-1].upper(),
                                 size_kb=round(uploaded.size / 1024, 1), status="ready", uploaded_by=current_user().get("id")))
                st.success("Document added.")
                st.rerun()
