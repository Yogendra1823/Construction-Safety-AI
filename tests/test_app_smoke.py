"""
Automated smoke tests for Construction Intelligence Hub.

Verifies every screen renders without raising an exception, using
Streamlit's built-in AppTest harness (no browser required).

Run from the project root:
    pip install -r requirements.txt
    python -m tests.test_app_smoke

Uses a throwaway local SQLite database (test_cih.db) so it never touches
your real MySQL data. Safe to run in CI.
"""
import os
import sys

os.environ["DB_ENGINE"] = "sqlite"
os.environ.setdefault("SECRET_KEY", "test-only-key")

db_file = "test_cih.db"
if os.path.exists(db_file):
    try:
        os.remove(db_file)
    except OSError:
        pass

# point sqlite at a throwaway file distinct from local dev usage
import config  # noqa: E402
config.SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file}"

from streamlit.testing.v1 import AppTest  # noqa: E402
from database.seed import seed_demo_data  # noqa: E402

PAGES = [
    "Dashboard", "Projects", "Client Requirement Analyzer", "Materials",
    "BOQ Generator", "Budget", "Workforce", "Equipment", "Inventory",
    "Safety", "AI Assistant", "Analytics", "Reports", "Documents",
    "Notifications", "Profile", "Admin Panel",
]
AUTH_PAGES = ["landing", "login", "register", "forgot"]

FAKE_USER = {"id": 1, "full_name": "Test Admin", "email": "admin@cihub.com",
             "role": "Project Manager", "is_admin": True, "department": "QA"}


def run():
    seed_demo_data()  # no-op if already seeded
    failures = []

    for page in PAGES:
        at = AppTest.from_file("app.py", default_timeout=60)
        at.session_state["auth_user"] = FAKE_USER
        at.session_state["page"] = page
        at.run()
        if at.exception:
            failures.append((page, at.exception[0]))

    for auth_page in AUTH_PAGES:
        at = AppTest.from_file("app.py", default_timeout=60)
        at.session_state["auth_page"] = auth_page
        at.run()
        if at.exception:
            failures.append((f"auth:{auth_page}", at.exception[0]))

    if failures:
        print(f"\n{len(failures)} SCREEN(S) FAILED:\n")
        for name, exc in failures:
            print(f"--- {name} ---\n{exc}\n")
        sys.exit(1)

    print(f"All {len(PAGES) + len(AUTH_PAGES)} screens rendered without errors.")


if __name__ == "__main__":
    run()
