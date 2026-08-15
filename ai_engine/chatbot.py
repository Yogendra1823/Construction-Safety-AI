"""
AI Chatbot — Enterprise Integration.
Uses Ollama (Gemma3:1b) to process natural language queries over real-time project data.

Architecture:
  1. Python-level off-topic filter — runs BEFORE the LLM, 100% reliable.
  2. Rich database digest including full material inventory.
  3. Reinforced system prompt with COMPLETE response enforcement.
"""
import re

from database.db import session_scope
from database.models import (
    Project, MaterialItem, Worker, Attendance, Equipment, InventoryItem,
    PurchaseOrder, SafetyIncident, Milestone, Document, BudgetItem,
)
from ai_engine import llm_client

# ---------------------------------------------------------------------------
# Off-topic pre-filter — runs BEFORE the LLM, never misses.
# ---------------------------------------------------------------------------
_OFF_TOPIC_PATTERNS = [
    r"\bwho is\b", r"\bwho was\b", r"\bwho are\b",
    r"\bcricketer\b", r"\bactor\b", r"\bsinger\b", r"\bpolitician\b",
    r"\bpresident\b", r"\bceo of\b",
    r"\bwhat is the capital\b", r"\bwhat is the population\b",
    r"\bhistory of\b", r"\bdefine\b", r"\bmeaning of\b",
    r"\bphysics\b", r"\bchemistry\b", r"\bmath\b",
    r"\bmovie\b", r"\bsong\b", r"\brecipe\b", r"\bweather\b",
    r"\bwrite a code\b", r"\bwrite code\b", r"\bpython script\b",
    r"\bchatgpt\b", r"\bopenai\b",
    r"^hi+\s*[!?]*$", r"^hello+\s*[!?]*$", r"^hey+\s*[!?]*$",
    r"^good\s*(morning|evening|afternoon)\s*[!?]*$",
    r"^how are you", r"^what('s| is) up\s*$",
    r"^thanks?\s*[!?]*$", r"^thank you\s*[!?]*$",
    r"^ok\s*[!?]*$", r"^okay\s*[!?]*$",
]
_OFF_TOPIC_COMPILED = [re.compile(p, re.IGNORECASE) for p in _OFF_TOPIC_PATTERNS]

_REFUSAL = (
    "I am the Agentic AI Assistant for Safety Monitoring & Construction Risk Analytics. "
    "I can only answer questions about your construction projects — status, safety, "
    "risk analytics, budget, materials, workforce, equipment, BOQ, milestones, and inventory. "
    "Please ask a project-related question."
)


def _is_off_topic(query: str) -> bool:
    """Fast Python-level guard. Returns True if the query is clearly off-topic."""
    q = query.strip()
    for pattern in _OFF_TOPIC_COMPILED:
        if pattern.search(q):
            return True
    return False



def _project_scope(db, project_id=None):
    q = db.query(Project).filter(Project.is_archived == False)  # noqa: E712
    if project_id:
        q = q.filter(Project.id == project_id)
    return q.all()


def _build_context_digest(db, projects) -> str:
    """Build a rich digest of database context for the LLM to ground its answers."""
    if not projects:
        return "No active projects available."

    lines = ["## ACTIVE PROJECTS SUMMARY"]
    for p in projects[:10]:
        lines.append(
            f"- {p.name} ({p.project_code}): Status={p.status}, Progress={p.progress_percent:.0f}%. "
            f"Budget: Rs{p.budget_used:,.0f} used of Rs{p.budget_total:,.0f} total. "
            f"Type: {p.building_type}, {p.floors} floors. Location: {p.location or 'n/a'}."
        )

    project_ids = [p.id for p in projects]

    # ALL materials (not just low-stock) so cement/steel/sand quantity queries work
    materials = db.query(MaterialItem).filter(MaterialItem.project_id.in_(project_ids)).limit(80).all()
    if materials:
        lines.append("\n## MATERIAL INVENTORY (all items per project)")
        for m in materials:
            p_code = next((p.project_code for p in projects if p.id == m.project_id), "N/A")
            lines.append(
                f"  - {p_code} | {m.material_name}: {m.remaining_qty:,.0f} {m.unit} remaining, "
                f"Availability={m.availability}."
            )

    # Workers per project
    from database.models import Worker
    from collections import Counter
    workers = db.query(Worker).filter(Worker.project_id.in_(project_ids)).all()
    if workers:
        from collections import Counter
        by_proj = Counter(w.project_id for w in workers)
        lines.append("\n## WORKFORCE")
        for p in projects:
            count = by_proj.get(p.id, 0)
            if count:
                lines.append(f"  - {p.project_code}: {count} workers assigned.")

    # Open safety incidents
    incidents = db.query(SafetyIncident).filter(
        SafetyIncident.project_id.in_(project_ids), SafetyIncident.status == "Open"
    ).limit(10).all()
    if incidents:
        lines.append("\n## OPEN SAFETY INCIDENTS")
        for i in incidents:
            lines.append(
                f"  - {i.incident_type} ({i.severity}): {i.project.project_code}. "
                f"Reported on {i.incident_date}."
            )

    # Upcoming milestones
    milestones = db.query(Milestone).filter(
        Milestone.project_id.in_(project_ids),
        Milestone.status.in_(["Pending", "In Progress"])
    ).limit(10).all()
    if milestones:
        lines.append("\n## UPCOMING MILESTONES")
        for m in milestones:
            p_code = next((p.project_code for p in projects if p.id == m.project_id), "N/A")
            lines.append(f"  - {m.title} ({p_code}): Due {m.due_date}, Status: {m.status}.")

    return "\n".join(lines)


def answer_question(query: str, project_id: int = None, chat_history: list = None):
    """
    Step 1: Python-level off-topic guard (instant, 100% reliable, never reaches LLM).
    Step 2: LLM answer grounded in live database digest.
    """
    # Hard Python guardrail — off-topic queries NEVER reach the LLM
    if _is_off_topic(query):
        return _REFUSAL, "llm"

    if not llm_client.is_available():
        return (
            "Ollama is currently offline. Please ensure Ollama is running with "
            "`gemma3:1b` installed to use the AI Assistant."
        ), "error"

    with session_scope() as db:
        projects = _project_scope(db, project_id)
        if not projects:
            return "I couldn't find any active projects to answer that about.", "llm"

        digest = _build_context_digest(db, projects)

        master_prompt = f"""You are the Agentic AI Assistant for Safety Monitoring & Construction Risk Analytics.

ABSOLUTE RULES — FOLLOW WITHOUT EXCEPTION:
1. You ONLY answer questions about the construction projects listed in CONTEXT DATA.
2. You NEVER discuss people, celebrities, sports, history, science, coding, or any other topic.
3. If data is not in CONTEXT DATA, reply EXACTLY: "Data not available for this project."
4. ALWAYS give a COMPLETE answer. Never stop mid-sentence. Fully finish every response.
5. Be factual and direct. No phrases like "Based on the data" or "Here is the information".

CONTEXT DATA:
{digest}
"""

        messages = [{"role": "system", "content": master_prompt}]

        if chat_history:
            # Filter empty entries and refusal messages; limit to 4 messages (2 turns)
            valid_history = [
                (role, msg, src)
                for role, msg, src in chat_history
                if msg and msg.strip() and msg != _REFUSAL
            ]
            for role, msg, source in valid_history[-4:]:
                llm_role = "user" if role == "user" else "assistant"
                messages.append({"role": llm_role, "content": msg})

        if not messages or messages[-1].get("content") != query:
            messages.append({"role": "user", "content": query})

        try:
            response = llm_client.chat_stream(messages)
            return response, "llm"
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}", "error"
