"""
Persistence audit: for every "add/update/save" action in the app, verify the
database was ACTUALLY changed — not just that no exception was raised. This
exists because of a real bug found during development: st.rerun() raises an
exception that a naive session context manager treated as an error and
rolled back, silently discarding every write made just before the rerun.
That bug is fixed (see database/db.py), but this test exists permanently to
make sure it — or anything like it — never comes back unnoticed.

Run:  python -m tests.test_persistence
"""
import os
import sys

os.environ["DB_ENGINE"] = "sqlite"
os.environ.setdefault("SECRET_KEY", "test-only-key")

db_file = "test_persistence.db"
if os.path.exists(db_file):
    try:
        os.remove(db_file)
    except OSError:
        pass

import config  # noqa: E402
config.SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file}"

from streamlit.testing.v1 import AppTest  # noqa: E402
from database.seed import seed_demo_data  # noqa: E402
from database.db import session_scope  # noqa: E402
from database.models import (  # noqa: E402
    Project, Worker, Attendance, Equipment, InventoryItem, PurchaseOrder,
    SafetyIncident, SafetyChecklistItem, BudgetItem, Expense, Notification,
    User, MaterialItem, Milestone,
)

FAKE_USER = {"id": 1, "full_name": "Admin User", "email": "admin@cihub.com",
             "role": "Project Manager", "is_admin": True, "department": "Ops"}

failures = []


def check(label, condition):
    if condition:
        print(f"OK   {label}")
    else:
        print(f"FAIL {label}")
        failures.append(label)


def fresh(page, project_id=None):
    at = AppTest.from_file("app.py", default_timeout=90)
    at.session_state["auth_user"] = FAKE_USER
    at.session_state["page"] = page
    if project_id is not None:
        at.session_state["active_project_id"] = project_id
    at.run()
    return at


def by_label(elements, label_substr):
    return next((e for e in elements if label_substr in (e.label or "")), None)


seed_demo_data()

with session_scope() as db:
    first_project = db.query(Project).first()
    first_project_id = first_project.id

# --- Workforce: add worker ---
before = None
with session_scope() as db:
    before = db.query(Worker).filter(Worker.name == "Persistence Test Worker").count()
at = fresh("Workforce", project_id=first_project_id)
name_field = by_label(at.text_input, "Full name")
name_field.input("Persistence Test Worker").run()
by_label(at.button, "Add Worker").click().run()
with session_scope() as db:
    after = db.query(Worker).filter(Worker.name == "Persistence Test Worker").count()
check("Workforce: add worker persists", after == before + 1)

# --- Equipment: add ---
at = fresh("Equipment")
name_field = by_label(at.text_input, "Equipment name")
name_field.input("Persistence Test Crane").run()
by_label(at.button, "Add Equipment").click().run()
with session_scope() as db:
    exists = db.query(Equipment).filter(Equipment.name == "Persistence Test Crane").first()
check("Equipment: add persists", exists is not None)

# --- Inventory: add item ---
at = fresh("Inventory")
name_field = by_label(at.text_input, "Item name")
name_field.input("Persistence Test Item").run()
by_label(at.button, "Add Item").click().run()
with session_scope() as db:
    exists = db.query(InventoryItem).filter(InventoryItem.item_name == "Persistence Test Item").first()
check("Inventory: add item persists", exists is not None)

# --- Inventory: create PO ---
at = fresh("Inventory")
supplier_field = by_label(at.text_input, "Supplier")
supplier_field.input("Persistence Test Supplier").run()
item_field = next(t for t in at.text_input if t.label == "Item")
item_field.input("Persistence Test Item PO").run()
by_label(at.button, "Create Purchase Order").click().run()
with session_scope() as db:
    exists = db.query(PurchaseOrder).filter(PurchaseOrder.supplier_name == "Persistence Test Supplier").first()
check("Inventory: purchase order persists", exists is not None)

# --- Safety: log incident ---
at = fresh("Safety", project_id=first_project_id)
itype_field = by_label(at.text_input, "Incident type")
itype_field.input("Persistence Test Incident").run()
by_label(at.button, "Log Incident").click().run()
with session_scope() as db:
    exists = db.query(SafetyIncident).filter(SafetyIncident.incident_type == "Persistence Test Incident").first()
check("Safety: log incident persists", exists is not None)

# --- Budget: log expense ---
with session_scope() as db:
    project = db.query(Project).filter(Project.id == first_project_id).first()
    budget_before = project.budget_used
at = fresh("Budget", project_id=first_project_id)
desc_field = by_label(at.text_input, "Description")
desc_field.input("Persistence Test Expense").run()
by_label(at.button, "Log Expense").click().run()
with session_scope() as db:
    expense_exists = db.query(Expense).filter(Expense.description == "Persistence Test Expense").first()
    project = db.query(Project).filter(Project.id == first_project_id).first()
check("Budget: expense row persists", expense_exists is not None)
check("Budget: project budget_used increments", project.budget_used > budget_before)

# --- Notifications: mark all read ---
with session_scope() as db:
    unread_before = db.query(Notification).filter(Notification.is_read == False).count()  # noqa: E712
at = fresh("Notifications")
mark_btn = by_label(at.button, "Mark all")
if mark_btn:
    mark_btn.click().run()
with session_scope() as db:
    unread_after = db.query(Notification).filter(Notification.is_read == False).count()  # noqa: E712
check("Notifications: mark-all-read persists", unread_before == 0 or unread_after < unread_before)

# --- Profile: edit ---
at = fresh("Profile")
fullname_field = by_label(at.text_input, "Full Name")
fullname_field.input("Persistence Test Name").run()
by_label(at.button, "Save Changes").click().run()
with session_scope() as db:
    user = db.query(User).filter(User.id == 1).first()
check("Profile: name change persists", user.full_name == "Persistence Test Name")

# --- Projects: progress update (attribute mutation, not just db.add) ---
at = fresh("Projects")
view_btn = by_label(at.button, "View")
view_btn.click().run()
opened_project_id = at.session_state["active_project_id"]
at.slider[0].set_value(77).run()
by_label(at.button, "Save Progress").click().run()
with session_scope() as db:
    p = db.query(Project).filter(Project.id == opened_project_id).first()
    proj_progress_ok = abs(p.progress_percent - 77) < 0.01
check("Projects: progress slider update persists", proj_progress_ok)

# --- Projects: add milestone ---
at2 = fresh("Projects")
view_btn2 = by_label(at2.button, "View")
view_btn2.click().run()
milestone_title = by_label(at2.text_input, "Milestone title")
milestone_title.input("Persistence Test Milestone").run()
by_label(at2.button, "Add Milestone").click().run()
with session_scope() as db:
    exists = db.query(Milestone).filter(Milestone.title == "Persistence Test Milestone").first()
check("Projects: add milestone persists", exists is not None)

print()
if failures:
    print(f"{len(failures)} CHECK(S) FAILED: {failures}")
    sys.exit(1)
print("ALL PERSISTENCE CHECKS PASSED")
