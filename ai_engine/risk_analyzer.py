"""
AI Risk Analysis — rolls budget, delay, material shortage and safety signals
into one composite project risk score, and a portfolio-level score for the
Command Center's "AI Risk Score" KPI.
"""


def compute_project_risk(budget_risk, delay_risk, material_risk, safety_risk):
    """All inputs 0-100. Weighted so schedule/budget dominate but safety
    incidents can still push a project into Critical on their own."""
    composite = (
        budget_risk * 0.30
        + delay_risk * 0.30
        + material_risk * 0.20
        + safety_risk * 0.20
    )
    composite = round(min(composite, 100), 1)

    if composite < 20:
        level = "Low"
    elif composite < 45:
        level = "Moderate"
    elif composite < 70:
        level = "High"
    else:
        level = "Critical"

    return composite, level, {
        "budget_risk": round(budget_risk, 1),
        "delay_risk": round(delay_risk, 1),
        "material_risk": round(material_risk, 1),
        "safety_risk": round(safety_risk, 1),
    }


def material_shortage_risk(materials):
    """materials: list of MaterialItem-like objects/dicts with estimated_qty,
    used_qty, availability. Returns 0-100."""
    if not materials:
        return 0
    flags = 0
    for m in materials:
        avail = m.availability if hasattr(m, "availability") else m.get("availability")
        usage_pct = m.usage_pct if hasattr(m, "usage_pct") else (
            (m.get("used_qty", 0) / m.get("estimated_qty", 1)) * 100 if m.get("estimated_qty") else 0
        )
        if avail == "Out of Stock":
            flags += 2
        elif avail == "Low":
            flags += 1
        if usage_pct > 90:
            flags += 1
    return min(flags * 12, 100)


def safety_risk_score(incidents):
    """incidents: list of SafetyIncident-like objects/dicts with severity and status."""
    if not incidents:
        return 0
    weight = {"Low": 6, "Medium": 14, "High": 26, "Critical": 45}
    score = 0
    for i in incidents:
        sev = i.severity if hasattr(i, "severity") else i.get("severity", "Low")
        status = i.status if hasattr(i, "status") else i.get("status", "Open")
        w = weight.get(sev, 6)
        score += w if status == "Open" else w * 0.35
    return min(round(score, 1), 100)
