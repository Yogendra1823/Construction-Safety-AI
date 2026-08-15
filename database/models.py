"""
SQLAlchemy ORM models for Construction Intelligence Hub.
One table per real-world entity referenced in the product spec. Every page
in the app reads/writes through these models rather than raw SQL, so the
schema here is the single source of truth for the whole system.
"""
from datetime import datetime, date

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime, Text,
    ForeignKey, UniqueConstraint, LargeBinary
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ------------------------------------------------------------------- Users --
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="Project Manager", index=True)
    phone = Column(String(30))
    department = Column(String(80), index=True)
    is_admin = Column(Boolean, default=False)
    theme = Column(String(20), default="dark")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    projects_created = relationship("Project", back_populates="creator")


# ---------------------------------------------------------------- Projects --
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    project_code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(160), nullable=False)
    client_name = Column(String(120))
    location = Column(String(160))
    building_type = Column(String(50))
    construction_style = Column(String(50))
    plot_size_sqft = Column(Float, default=0)
    plot_length_ft = Column(Float, default=0)
    plot_width_ft = Column(Float, default=0)
    floors = Column(Integer, default=1)
    bedrooms = Column(Integer, default=0)
    bathrooms = Column(Integer, default=0)
    kitchens = Column(Integer, default=1)
    parking_spots = Column(Integer, default=0)
    material_quality = Column(String(20), default="Standard")

    budget_total = Column(Float, default=0)
    budget_used = Column(Float, default=0)

    start_date = Column(Date, default=date.today)
    expected_completion = Column(Date)
    actual_completion = Column(Date)

    status = Column(String(20), default="Planning", index=True)
    progress_percent = Column(Float, default=0)
    risk_score = Column(Float, default=0)          # 0-100, higher = riskier
    is_archived = Column(Boolean, default=False, index=True)

    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User", back_populates="projects_created")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    materials = relationship("MaterialItem", back_populates="project", cascade="all, delete-orphan")
    budget_items = relationship("BudgetItem", back_populates="project", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    team = relationship("TeamAssignment", back_populates="project", cascade="all, delete-orphan")
    
    # Missing cascades added for Database Hardening:
    safety_incidents = relationship("SafetyIncident", back_populates="project", cascade="all, delete-orphan")
    safety_checklists = relationship("SafetyChecklistItem", back_populates="project", cascade="all, delete-orphan")
    progress_logs = relationship("ProgressLog", back_populates="project", cascade="all, delete-orphan")
    ai_recommendations = relationship("AIRecommendation", back_populates="project", cascade="all, delete-orphan")
    equipment = relationship("Equipment", back_populates="project", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="project", cascade="all, delete-orphan")
    workers = relationship("Worker", back_populates="project", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="project", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="project", cascade="all, delete-orphan")


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(160), nullable=False)
    due_date = Column(Date)
    completed_date = Column(Date)
    status = Column(String(20), default="Pending", index=True)

    project = relationship("Project", back_populates="milestones")


class TeamAssignment(Base):
    __tablename__ = "team_assignments"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_on_project = Column(String(80))

    project = relationship("Project", back_populates="team")
    user = relationship("User")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(60))
    category_source = Column(String(10), default="manual") 
    size_kb = Column(Float, default=0)
    status = Column(String(20), default="ready")
    content = Column(LargeBinary)
    mime_type = Column(String(120), default="application/octet-stream")
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="documents")


# --------------------------------------------------------------- Materials --
class MaterialItem(Base):
    __tablename__ = "material_items"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    material_name = Column(String(80), nullable=False)
    category = Column(String(40))
    unit = Column(String(20))
    estimated_qty = Column(Float, default=0)
    used_qty = Column(Float, default=0)
    unit_cost = Column(Float, default=0)
    supplier = Column(String(120))
    availability = Column(String(20), default="In Stock")

    project = relationship("Project", back_populates="materials")

    @property
    def remaining_qty(self):
        return max(self.estimated_qty - self.used_qty, 0)

    @property
    def usage_pct(self):
        return round((self.used_qty / self.estimated_qty) * 100, 1) if self.estimated_qty else 0

    @property
    def total_cost(self):
        return round(self.estimated_qty * self.unit_cost, 2)


# ------------------------------------------------------------------ Budget --
class BudgetItem(Base):
    __tablename__ = "budget_items"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(40))
    allocated_amount = Column(Float, default=0)
    spent_amount = Column(Float, default=0)

    project = relationship("Project", back_populates="budget_items")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(40))
    description = Column(String(200))
    amount = Column(Float, default=0)
    expense_date = Column(Date, default=date.today)
    recorded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    project = relationship("Project", back_populates="expenses")


# --------------------------------------------------------------- Workforce --
class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    role = Column(String(60))
    phone = Column(String(30))
    daily_wage = Column(Float, default=0)
    status = Column(String(20), default="Active")
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)

    project = relationship("Project", back_populates="workers")
    attendance = relationship("Attendance", back_populates="worker", cascade="all, delete-orphan")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    work_date = Column(Date, default=date.today)
    status = Column(String(20), default="Present")
    hours_worked = Column(Float, default=8)

    worker = relationship("Worker", back_populates="attendance")
    project = relationship("Project")


# --------------------------------------------------------------- Equipment --
class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    equipment_type = Column(String(50))
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    status = Column(String(20), default="Available")
    fuel_level = Column(Float, default=100)
    usage_hours = Column(Float, default=0)
    last_maintenance = Column(Date)
    next_maintenance = Column(Date)

    project = relationship("Project", back_populates="equipment")


# ---------------------------------------------------------------- Inventory --
class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True)
    item_name = Column(String(120), nullable=False)
    category = Column(String(50))
    quantity_in_stock = Column(Float, default=0)
    unit = Column(String(20))
    reorder_level = Column(Float, default=0)
    warehouse_location = Column(String(80))


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    supplier_name = Column(String(120))
    item_name = Column(String(120))
    quantity = Column(Float, default=0)
    unit_cost = Column(Float, default=0)
    order_date = Column(Date, default=date.today)
    expected_delivery = Column(Date)
    status = Column(String(20), default="Pending")

    project = relationship("Project", back_populates="purchase_orders")


# ------------------------------------------------------------------ Safety --
class SafetyIncident(Base):
    __tablename__ = "safety_incidents"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    incident_type = Column(String(80))
    severity = Column(String(20), default="Low")
    description = Column(Text)
    incident_date = Column(Date, default=date.today)
    status = Column(String(20), default="Open")
    reported_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    project = relationship("Project", back_populates="safety_incidents")


class SafetyChecklistItem(Base):
    __tablename__ = "safety_checklist_items"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    item_name = Column(String(120))
    category = Column(String(40))
    status = Column(String(20), default="Pending")
    checked_date = Column(Date, default=date.today)

    project = relationship("Project", back_populates="safety_checklists")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True)
    name = Column(String(120))
    role = Column(String(80))
    phone = Column(String(30))
    contact_type = Column(String(40))


# ------------------------------------------------------------- Notifications --
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    notif_type = Column(String(30))
    message = Column(String(255))
    severity = Column(String(20), default="info")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="notifications")


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    action = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    project = relationship("Project", back_populates="activity_logs")


class ProgressLog(Base):
    __tablename__ = "progress_log"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    log_date = Column(Date, default=date.today)
    actual_progress_pct = Column(Float, default=0)
    planned_progress_pct = Column(Float, default=0)

    project = relationship("Project", back_populates="progress_logs")


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    category = Column(String(40))
    message = Column(String(255))
    impact = Column(String(20), default="Medium")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="ai_recommendations")
