"""
AI Material Estimation + Smart Area Planner.

Material quantities are derived from published construction thumb rules
(config.MATERIAL_THUMB_RULES), scaled by a quality multiplier and a small
random-forest-free adjustment for floor count (higher floors need
proportionally more structural steel/concrete for load-bearing).
"""
from config import MATERIAL_THUMB_RULES, MATERIAL_UNIT_COST_INR, MATERIAL_QUALITY_LEVELS

QUALITY_MATERIAL_MULTIPLIER = {"Basic": 0.92, "Standard": 1.0, "Premium": 1.18}

MATERIAL_UNITS = {
    "Cement": "bags", "Steel": "kg", "Sand": "cft", "Bricks": "units",
    "Concrete": "cft", "Tiles": "sqft", "Paint": "litres",
    "Electrical": "points", "Plumbing": "points", "Roofing": "sqft", "Flooring": "sqft",
}


def estimate_materials(plot_size_sqft: float, floors: int, quality: str = "Standard"):
    """Returns a list of dicts: material_name, unit, quantity, unit_cost, total_cost."""
    q_mult = QUALITY_MATERIAL_MULTIPLIER.get(quality, 1.0)
    floor_mult = 1 + max(floors - 1, 0) * 0.08  # more structure per extra floor
    built_up_area = plot_size_sqft * floors

    rules = MATERIAL_THUMB_RULES
    raw = {
        "Cement": built_up_area * rules["cement_bags_per_sqft"] * floor_mult,
        "Steel": built_up_area * rules["steel_kg_per_sqft"] * floor_mult,
        "Sand": built_up_area * rules["sand_cft_per_sqft"],
        "Bricks": built_up_area * rules["bricks_per_sqft"],
        "Concrete": built_up_area * rules["concrete_cft_per_sqft"] * floor_mult,
        "Tiles": built_up_area * rules["tiles_sqft_per_sqft"] * q_mult,
        "Paint": built_up_area * rules["paint_litre_per_sqft"] * q_mult,
        "Electrical": built_up_area * rules["electrical_points_per_sqft"] * q_mult,
        "Plumbing": built_up_area * rules["plumbing_points_per_sqft"],
        "Roofing": plot_size_sqft * 1.0,
        "Flooring": built_up_area * q_mult,
    }

    results = []
    for name, qty in raw.items():
        unit_cost = MATERIAL_UNIT_COST_INR[name] * (1.15 if quality == "Premium" else (0.95 if quality == "Basic" else 1.0))
        qty = round(qty, 1)
        results.append({
            "material_name": name,
            "category": "Structural" if name in ("Cement", "Steel", "Sand", "Bricks", "Concrete") else "Finishing",
            "unit": MATERIAL_UNITS[name],
            "estimated_qty": qty,
            "unit_cost": round(unit_cost, 2),
            "total_cost": round(qty * unit_cost, 2),
        })
    return results


def plan_areas(plot_size_sqft: float, bedrooms: int, bathrooms: int, kitchens: int, parking_spots: int, floors: int = 1):
    """Smart Area Planner — auto-allocates carpet area across room types and
    validates the allocation fits within the buildable area (assumes ~65%
    carpet efficiency after walls/circulation, standard for RCC framed
    construction)."""
    buildable_area = plot_size_sqft * floors * 0.65

    allocations = []
    living_room = max(180, buildable_area * 0.16)
    allocations.append(("Living Room", 1, living_room))

    bedroom_size = 140
    allocations.append(("Bedrooms", bedrooms, bedroom_size * bedrooms))

    bathroom_size = 45
    allocations.append(("Bathrooms", bathrooms, bathroom_size * bathrooms))

    kitchen_size = 110
    allocations.append(("Kitchen", kitchens, kitchen_size * kitchens))

    balcony_size = 60
    n_balconies = max(1, bedrooms // 2)
    allocations.append(("Balcony", n_balconies, balcony_size * n_balconies))

    parking_size = 130
    allocations.append(("Parking", parking_spots, parking_size * parking_spots))

    allocated_total = sum(a[2] for a in allocations)
    circulation = buildable_area * 0.12  # corridors/stairs
    allocated_total += circulation

    is_valid = allocated_total <= buildable_area * 1.05  # 5% tolerance
    utilization_pct = round((allocated_total / buildable_area) * 100, 1) if buildable_area else 0

    rows = [
        {"room": name, "count": count, "sqft": round(sqft, 0)}
        for name, count, sqft in allocations
    ]
    rows.append({"room": "Circulation & Walls", "count": "-", "sqft": round(circulation, 0)})

    return {
        "buildable_area": round(buildable_area, 0),
        "allocated_total": round(allocated_total, 0),
        "utilization_pct": utilization_pct,
        "is_valid": is_valid,
        "rows": rows,
    }
