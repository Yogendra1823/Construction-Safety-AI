"""
AI Workforce Prediction — suggests headcount by role based on built-up area,
floors and building type, using labour-productivity ratios common in Indian
residential/commercial construction (sqft handled per worker per project
phase). Ratios are deliberately conservative averages across a project's
full duration, not a single day's crew size.
"""
ROLE_SQFT_RATIO = {
    # role: sqft of built-up area one worker of this role typically covers
    # across the life of the project
    "Labourer": 90,
    "Mason": 160,
    "Site Engineer": 1400,
    "Electrician": 550,
    "Plumber": 650,
    "Painter": 400,
    "Carpenter": 500,
    "Welder": 900,
    "Supervisor": 2200,
}

COMPLEX_BUILDING_TYPES = {"Hospital", "Commercial Complex", "Office"}


def suggest_workforce(plot_size_sqft: float, floors: int, building_type: str = "House"):
    built_up_area = plot_size_sqft * floors
    complexity_mult = 1.25 if building_type in COMPLEX_BUILDING_TYPES else 1.0

    suggestions = []
    total = 0
    for role, ratio in ROLE_SQFT_RATIO.items():
        count = max(1, round((built_up_area * complexity_mult) / ratio))
        suggestions.append({"role": role, "suggested_count": count})
        total += count

    return {"total_workforce": total, "by_role": suggestions, "built_up_area": round(built_up_area, 0)}
