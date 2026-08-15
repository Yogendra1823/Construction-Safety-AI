"""
Central configuration for Construction Intelligence Hub.
Loads secrets from .env and exposes app-wide constants (colors, thresholds, etc.)
so every module pulls from one source of truth.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------- Database --
DB_ENGINE = os.getenv("DB_ENGINE", "mysql").lower()

if DB_ENGINE == "sqlite":
    SQLALCHEMY_DATABASE_URL = "sqlite:///cih_local.db"
else:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "cih_db")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-insecure-key-change-me")

# ------------------------------------------------------- Local LLM (Ollama) --
# Optional, fully local, no API key. Powers the AI Assistant's free-form
# chat fallback and (when available) a more natural AI Summary. If Ollama
# isn't running, every feature in the app still works — this is additive.
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "true").lower() in ("1", "true", "yes")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")

# ------------------------------------------------------------- App identity --
APP_NAME = "Agentic AI Safety & Risk"
APP_FULL_NAME = "Agentic AI for Safety Monitoring with Construction Risk Analytics"
APP_TAGLINE = "Agentic AI for Safety Monitoring with Construction Risk Analytics"
APP_VERSION = "1.0"

# ------------------------------------------------------------------- Theme --
# "Site Blueprint" design system — dark mode evokes a blueprint laid out on
# a light table at night; light mode evokes the same drawing printed on
# drafting paper. Both share the same structure (grid background, corner
# brackets on cards, monospace data readouts) so switching themes never
# changes the app's visual language, only its lighting.
COLOR_THEMES = {
    "dark": {
        "bg": "#0D1117",
        "bg_card": "#161B22",
        "bg_card_alt": "#1C2333",
        "border": "#30363D",
        "grid_line": "rgba(88, 166, 255, 0.05)",
        "primary": "#58A6FF",
        "primary_dark": "#1F6FEB",
        "accent": "#F78166",
        "success": "#3FB950",
        "warning": "#D29922",
        "danger": "#F85149",
        "text": "#E6EDF3",
        "text_dim": "#8B949E",
        "text_faint": "#484F58",
        "shadow": "rgba(0,0,0,0.5)",
    },
    "light": {
        "bg": "#F1F5F9",
        "bg_card": "#FFFFFF",
        "bg_card_alt": "#F8FAFC",
        "border": "#E2E8F0",
        "grid_line": "rgba(37, 99, 235, 0.04)",
        "primary": "#2563EB",
        "primary_dark": "#1D4ED8",
        "accent": "#EA580C",
        "success": "#059669",
        "warning": "#D97706",
        "danger": "#DC2626",
        "text": "#0F172A",
        "text_dim": "#475569",
        "text_faint": "#94A3B8",
        "shadow": "rgba(15,23,42,0.08)",
    },
}
DEFAULT_THEME = "light"

# ------------------------------------------------------------ Business rules --
# Rule-of-thumb construction estimation factors (industry thumb rules for
# basic RCC-frame residential/commercial construction in India). These power
# the estimator engines until real historical project data is available to
# train proper regression models.
MATERIAL_THUMB_RULES = {
    "cement_bags_per_sqft": 0.40,
    "steel_kg_per_sqft": 4.5,
    "sand_cft_per_sqft": 1.6,
    "bricks_per_sqft": 8.5,
    "concrete_cft_per_sqft": 0.55,
    "tiles_sqft_per_sqft": 0.95,
    "paint_litre_per_sqft": 0.045,
    "electrical_points_per_sqft": 0.045,
    "plumbing_points_per_sqft": 0.02,
}

MATERIAL_UNIT_COST_INR = {
    "Cement": 380,       # per bag
    "Steel": 68,         # per kg
    "Sand": 55,           # per cft
    "Bricks": 9,          # per piece
    "Concrete": 145,      # per cft (ready mix)
    "Tiles": 65,           # per sqft
    "Paint": 260,          # per litre
    "Electrical": 450,     # per point
    "Plumbing": 650,       # per point
    "Roofing": 90,          # per sqft
    "Flooring": 110,        # per sqft
}

COST_PER_SQFT_BY_QUALITY = {
    "Basic": 1450,
    "Standard": 1950,
    "Premium": 2650,
}

BUILDING_TYPES = ["House", "Villa", "Apartment", "Office", "Commercial Complex", "School", "Warehouse", "Hospital"]
CONSTRUCTION_STYLES = ["Modern", "Traditional", "Contemporary", "Minimalist", "Industrial", "Colonial"]
MATERIAL_QUALITY_LEVELS = ["Basic", "Standard", "Premium"]
PROJECT_STATUSES = ["Planning", "Ongoing", "Delayed", "On Hold", "Completed"]
WORKER_ROLES = ["Site Engineer", "Contractor", "Mason", "Electrician", "Plumber", "Painter", "Labourer", "Carpenter", "Welder", "Supervisor"]
EQUIPMENT_TYPES = ["Crane", "Concrete Mixer", "Truck", "Excavator", "Bulldozer", "Loader", "Generator", "Scaffolding Unit"]
