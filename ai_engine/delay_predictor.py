"""
AI Delay Prediction.

Combines schedule variance (actual progress vs. where the project should be
given elapsed time), workforce attendance rate, and material delivery
health into a single 0-100 delay-risk score. Weather is left as a stub
input for the future weather-API integration mentioned in the roadmap.
"""
from datetime import date


def _expected_progress_pct(start_date, expected_completion, today=None):
    today = today or date.today()
    if not start_date or not expected_completion or expected_completion <= start_date:
        return 0
    total_days = (expected_completion - start_date).days
    elapsed_days = (today - start_date).days
    return max(0, min(100, (elapsed_days / total_days) * 100))


def predict_delay_risk(start_date, expected_completion, actual_progress_pct,
                        attendance_rate_pct=100, material_delay_flags=0, weather_risk=0):
    """
    attendance_rate_pct: % of expected workers present over the last period
    material_delay_flags: count of materials currently behind delivery schedule
    weather_risk: 0-100, reserved for future weather integration (defaults 0)
    Returns (risk_score 0-100, level, expected_progress_pct)
    """
    expected = _expected_progress_pct(start_date, expected_completion)
    schedule_gap = max(expected - actual_progress_pct, 0)  # how far behind schedule

    schedule_risk = min(schedule_gap * 2.2, 100)
    attendance_risk = min(max(100 - attendance_rate_pct, 0) * 1.3, 100)
    material_risk = min(material_delay_flags * 18, 100)

    composite = (
        schedule_risk * 0.55
        + attendance_risk * 0.25
        + material_risk * 0.15
        + weather_risk * 0.05
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

    return composite, level, round(expected, 1)
