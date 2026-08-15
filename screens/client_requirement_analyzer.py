from datetime import date, timedelta

import pandas as pd
import streamlit as st

from ai_engine.cost_predictor import predict_cost
from ai_engine.material_estimator import estimate_materials, plan_areas
from ai_engine import llm_client
from config import BUILDING_TYPES, CONSTRUCTION_STYLES, MATERIAL_QUALITY_LEVELS, OLLAMA_MODEL
from utils.styling import section_header, status_badge, card_open, card_close, kpi_card


def _timeline_weeks(plot_size, floors, building_type):
    base = (plot_size * floors) / 260  # sqft handled per week, rough industry pace
    complexity = 1.3 if building_type in ("Hospital", "Commercial Complex", "Office") else 1.0
    return max(6, round(base * complexity))


def _risk_level(budget, estimated_cost, timeline_weeks):
    overrun_pct = ((estimated_cost - budget) / budget * 100) if budget else 0
    score = max(overrun_pct, 0) * 0.8 + max(timeline_weeks - 40, 0) * 0.5
    if score < 10:
        return "Low", score
    elif score < 30:
        return "Moderate", score
    elif score < 60:
        return "High", score
    return "Critical", score


def _llm_polish_summary(template_text: str, predicted_cost: float):
    """Optionally rewrites the templated summary in more natural language via
    the local LLM. Never trusted blindly: if the rewritten text drops the
    exact cost figure, we discard it and keep the deterministic template —
    a small local model is for phrasing, not for the numbers."""
    if not llm_client.is_available():
        return None
    system = (
        "Rewrite the following construction project summary to sound natural "
        "and professional, in 2-3 sentences. You MUST keep every number, "
        "currency figure and percentage EXACTLY as given — do not change, "
        "round, or invent any numbers, and do not add facts not already present."
    )
    messages = [{"role": "system", "content": system}, {"role": "user", "content": template_text}]
    polished = llm_client.chat(messages, temperature=0.5)
    if not polished:
        return None
    if f"{predicted_cost:,.0f}" not in polished:
        return None  # failed the numeric-integrity check — don't risk it
    return polished


def render():
    section_header("Client Requirement Analyzer", "Turn a client's brief into a cost, material and timeline estimate")

    with st.form("cra_form"):
        c1, c2 = st.columns(2)
        with c1:
            plot_size = st.number_input("Plot Size (sqft)", min_value=200.0, value=1800.0, step=50.0)
            plot_length = st.number_input("Plot Length (ft)", min_value=0.0, value=45.0, step=1.0)
            plot_width = st.number_input("Plot Width (ft)", min_value=0.0, value=40.0, step=1.0)
            building_type = st.selectbox("Building Type", BUILDING_TYPES)
            floors = st.number_input("Floors", min_value=1, value=2, step=1)
            bedrooms = st.number_input("Bedrooms", min_value=0, value=3, step=1)
        with c2:
            bathrooms = st.number_input("Bathrooms", min_value=0, value=3, step=1)
            kitchens = st.number_input("Kitchens", min_value=0, value=1, step=1)
            parking = st.number_input("Parking Spots", min_value=0, value=2, step=1)
            budget = st.number_input("Client Budget (₹)", min_value=0.0, value=3500000.0, step=50000.0)
            style = st.selectbox("Construction Style", CONSTRUCTION_STYLES)
            quality = st.selectbox("Construction Quality", MATERIAL_QUALITY_LEVELS, index=1)
        expected_completion = st.date_input("Client's Expected Completion", value=date.today() + timedelta(weeks=30))

        submitted = st.form_submit_button("Analyze Requirement", type="primary")

    if not submitted:
        return

    predicted_cost, low, high, cost_per_sqft = predict_cost(plot_size, floors, building_type, quality, style)
    weeks = _timeline_weeks(plot_size, floors, building_type)
    risk_level, risk_score = _risk_level(budget, predicted_cost, weeks)
    materials = estimate_materials(plot_size, floors, quality)
    area_plan = plan_areas(plot_size, bedrooms, bathrooms, kitchens, parking, floors)

    st.write("")
    section_header("AI Summary")
    fit_note = "within" if predicted_cost <= budget * 1.05 else "above"
    template_summary = (
        f"A {floors}-floor {building_type.lower()} on a {plot_size:,.0f} sqft plot in {style.lower()} style, "
        f"built to {quality} quality, is estimated at ₹{predicted_cost:,.0f} — {fit_note} the client's "
        f"₹{budget:,.0f} budget. Expect roughly {weeks} weeks to completion, with an overall risk "
        f"level of {risk_level} based on budget fit and timeline length."
    )
    polished = _llm_polish_summary(template_summary, predicted_cost)
    st.markdown(polished or template_summary)
    if polished:
        st.caption(f"Phrased by {OLLAMA_MODEL} (local) · numbers verified against the deterministic AI models above")

    st.write("")
    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_card("Estimated Cost", f"₹{predicted_cost:,.0f}", "💰", accent="primary")
    with k2: kpi_card("Cost Range", f"₹{low/1e5:,.1f}L–₹{high/1e5:,.1f}L", "📐", accent="primary")
    with k3: kpi_card("Suggested Timeline", f"{weeks} weeks", "🗓️", accent="warning")
    risk_accent = {"Low": "success", "Moderate": "warning", "High": "danger", "Critical": "danger"}[risk_level]
    with k4: kpi_card("Risk Level", risk_level, "🧠", accent=risk_accent)

    st.write("")
    left, right = st.columns([1.3, 1])
    with left:
        with st.container(border=True):
            section_header("Material Requirement", "AI-estimated quantities for this brief")
            df = pd.DataFrame(materials)[["material_name", "unit", "estimated_qty", "unit_cost", "total_cost"]]
            df.columns = ["Material", "Unit", "Est. Quantity", "Unit Cost (₹)", "Total Cost (₹)"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Total material cost: ₹{sum(m['total_cost'] for m in materials):,.0f}")

    with right:
        with st.container(border=True):
            section_header("Smart Area Planner", "Auto-allocated room breakdown, validated against buildable area")
            df_a = pd.DataFrame(area_plan["rows"])
            df_a.columns = ["Room", "Count", "Sqft"]
            st.dataframe(df_a, use_container_width=True, hide_index=True)
            badge = status_badge("Allocation fits buildable area", "success") if area_plan["is_valid"] else status_badge("Over-allocated — reduce room sizes or add a floor", "danger")
            st.markdown(badge, unsafe_allow_html=True)
            st.caption(f"Utilization: {area_plan['utilization_pct']}% of {area_plan['buildable_area']:,.0f} sqft buildable area")

    st.caption(
        "Estimates are generated by the AI cost and material models trained on construction industry "
        "thumb rules — treat as a planning baseline, not a final quotation."
    )
