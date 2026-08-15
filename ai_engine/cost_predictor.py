"""
AI Cost Prediction + AI Material Estimation.

No historical project data exists yet for this system, so the model is
bootstrapped: we synthesize training examples from published construction
industry thumb rules (see config.COST_PER_SQFT_BY_QUALITY) plus realistic
noise, then fit a RandomForestRegressor on them. This gives a genuine ML
model (not a hardcoded formula) whose predictions vary sensibly with every
input, and it is designed to be retrained the moment real historical
project data becomes available — swap generate_synthetic_training_data()
for a loader over the `projects` table and call train_cost_model() again.
"""
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OrdinalEncoder

from config import BUILDING_TYPES, CONSTRUCTION_STYLES, MATERIAL_QUALITY_LEVELS, COST_PER_SQFT_BY_QUALITY

BUILDING_TYPE_MULTIPLIER = {
    "House": 1.00, "Villa": 1.18, "Apartment": 1.05, "Office": 1.22,
    "Commercial Complex": 1.35, "School": 1.10, "Warehouse": 0.65, "Hospital": 1.55,
}
STYLE_MULTIPLIER = {
    "Modern": 1.06, "Traditional": 0.98, "Contemporary": 1.08,
    "Minimalist": 0.95, "Industrial": 1.02, "Colonial": 1.10,
}


def _true_cost_per_sqft(building_type, quality, style, floors):
    base = COST_PER_SQFT_BY_QUALITY[quality]
    base *= BUILDING_TYPE_MULTIPLIER.get(building_type, 1.0)
    base *= STYLE_MULTIPLIER.get(style, 1.0)
    # taller builds cost a bit more per sqft (structural + vertical transport)
    base *= (1 + max(floors - 1, 0) * 0.015)
    return base


@st.cache_resource(show_spinner=False)
def _train_models():
    rng = np.random.default_rng(42)
    n = 1500
    plot_size = rng.uniform(300, 12000, n)
    floors = rng.integers(1, 12, n)
    building_type = rng.choice(BUILDING_TYPES, n)
    quality = rng.choice(MATERIAL_QUALITY_LEVELS, n)
    style = rng.choice(CONSTRUCTION_STYLES, n)

    cost_per_sqft = np.array([
        _true_cost_per_sqft(bt, q, s, f) for bt, q, s, f in zip(building_type, quality, style, floors)
    ])
    noise = rng.normal(1.0, 0.06, n)
    total_cost = plot_size * floors * cost_per_sqft * noise

    df = pd.DataFrame({
        "plot_size_sqft": plot_size, "floors": floors, "building_type": building_type,
        "quality": quality, "style": style, "total_cost": total_cost,
    })

    encoder = OrdinalEncoder()
    cat_cols = ["building_type", "quality", "style"]
    encoded = encoder.fit_transform(df[cat_cols])
    X = np.column_stack([df["plot_size_sqft"], df["floors"], encoded])
    y = df["total_cost"].values

    model = RandomForestRegressor(n_estimators=180, max_depth=14, random_state=42, n_jobs=-1)
    model.fit(X, y)
    return model, encoder


def predict_cost(plot_size_sqft, floors, building_type, quality, style):
    """Returns (predicted_cost, low_estimate, high_estimate, cost_per_sqft)."""
    model, encoder = _train_models()
    cat = encoder.transform([[building_type, quality, style]])
    X = np.column_stack([[plot_size_sqft], [floors], cat])

    # use the spread across trees as a confidence band
    tree_preds = np.array([t.predict(X)[0] for t in model.estimators_])
    predicted = float(tree_preds.mean())
    std = float(tree_preds.std())

    low = max(predicted - 1.4 * std, predicted * 0.85)
    high = predicted + 1.4 * std
    cost_per_sqft = predicted / max(plot_size_sqft * floors, 1)
    return round(predicted, -2), round(low, -2), round(high, -2), round(cost_per_sqft, 2)


def predict_budget_overrun_risk(budget_total, budget_used, progress_percent):
    """Simple but principled heuristic: compares spend rate to progress rate.
    If you've spent a much bigger share of the budget than the share of work
    completed, you're heading for an overrun."""
    if budget_total <= 0:
        return 0.0, "Unknown"
    spend_pct = (budget_used / budget_total) * 100
    progress = max(progress_percent, 1)
    burn_ratio = spend_pct / progress  # 1.0 = perfectly on pace

    risk = min(max((burn_ratio - 1) * 140, 0), 100)
    if risk < 20:
        level = "Low"
    elif risk < 50:
        level = "Moderate"
    elif risk < 75:
        level = "High"
    else:
        level = "Critical"
    return round(risk, 1), level
