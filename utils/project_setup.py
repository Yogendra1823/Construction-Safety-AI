import datetime
from sqlalchemy.orm import Session
from database.models import Project, BudgetItem, MaterialItem, Worker, Equipment, Milestone, TeamAssignment
from config import MATERIAL_THUMB_RULES, MATERIAL_UNIT_COST_INR

def bootstrap_new_project(db: Session, project: Project):
    """
    Intelligently bootstraps a new project with default budget allocations, 
    materials, workforce, equipment, and milestones based on industry heuristics.
    """
    total_sqft = project.plot_size_sqft * project.floors
    
    # --------------------------------------------------------- 1. Budget Allocation
    allocations = {
        "Materials": 0.55,
        "Labor": 0.25,
        "Equipment": 0.10,
        "Overhead": 0.05,
        "Contingency": 0.05
    }
    
    for category, pct in allocations.items():
        b_item = BudgetItem(
            project_id=project.id,
            category=category,
            allocated_amount=project.budget_total * pct,
            spent_amount=0
        )
        db.add(b_item)

    # --------------------------------------------------------- 2. Materials
    material_mappings = [
        ("cement_bags_per_sqft", "Cement", "Bags", "Cement"),
        ("steel_kg_per_sqft", "Steel (Rebar)", "kg", "Steel"),
        ("sand_cft_per_sqft", "Sand", "cft", "Sand"),
        ("bricks_per_sqft", "Bricks", "pcs", "Bricks"),
        ("concrete_cft_per_sqft", "Ready Mix Concrete", "cft", "Concrete"),
        ("tiles_sqft_per_sqft", "Tiles", "sqft", "Tiles"),
        ("paint_litre_per_sqft", "Paint", "litres", "Paint"),
        ("electrical_points_per_sqft", "Electrical Fittings", "points", "Electrical"),
        ("plumbing_points_per_sqft", "Plumbing Fittings", "points", "Plumbing"),
    ]

    for rule_key, mat_name, unit, cost_key in material_mappings:
        multiplier = MATERIAL_THUMB_RULES.get(rule_key, 0)
        est_qty = total_sqft * multiplier
        unit_cost = MATERIAL_UNIT_COST_INR.get(cost_key, 0)
        
        if est_qty > 0:
            m_item = MaterialItem(
                project_id=project.id,
                material_name=mat_name,
                category="Primary" if cost_key in ["Cement", "Steel", "Sand", "Bricks", "Concrete"] else "Finishing",
                unit=unit,
                estimated_qty=round(est_qty, 2),
                used_qty=0,
                unit_cost=unit_cost,
                availability="In Stock"
            )
            db.add(m_item)

    # --------------------------------------------------------- 3. Workforce
    db.add(Worker(name="Default Site Engineer", role="Site Engineer", daily_wage=1500, project_id=project.id))
    db.add(Worker(name="Default Supervisor", role="Supervisor", daily_wage=1200, project_id=project.id))
    
    num_masons = max(1, int(total_sqft // 500))
    num_labourers = num_masons * 2
    
    for i in range(num_masons):
        db.add(Worker(name=f"Mason {i+1}", role="Mason", daily_wage=800, project_id=project.id))
    for i in range(num_labourers):
        db.add(Worker(name=f"Labourer {i+1}", role="Labourer", daily_wage=500, project_id=project.id))

    # --------------------------------------------------------- 3.5 Team Assignments
    if project.created_by:
        db.add(TeamAssignment(project_id=project.id, user_id=project.created_by, role_on_project="Project Manager"))

    # --------------------------------------------------------- 4. Equipment
    if project.floors >= 2:
        db.add(Equipment(name="Heavy Duty Crane", equipment_type="Crane", project_id=project.id, status="Available"))
    if total_sqft > 1000:
        db.add(Equipment(name="Site Concrete Mixer", equipment_type="Concrete Mixer", project_id=project.id, status="Available"))
        
    num_scaffolding = max(1, project.floors)
    for i in range(num_scaffolding):
        db.add(Equipment(name=f"Scaffolding Unit {i+1}", equipment_type="Scaffolding Unit", project_id=project.id, status="Available"))

    # --------------------------------------------------------- 5. Milestones
    start = project.start_date
    end = project.expected_completion
    
    if not end:
        end = start + datetime.timedelta(days=180)
        
    total_days = (end - start).days
    
    default_milestones = [
        ("Site Preparation", 0.1),
        ("Foundation Completed", 0.25),
        ("Superstructure Erected", 0.5),
        ("Finishing Works", 0.8),
        ("Handover & Signoff", 1.0)
    ]
    
    for title, pct in default_milestones:
        due = start + datetime.timedelta(days=int(total_days * pct))
        m_item = Milestone(
            project_id=project.id,
            title=title,
            due_date=due,
            status="Pending"
        )
        db.add(m_item)
        
    db.flush()
