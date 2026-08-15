# Agentic AI for Safety Monitoring with Construction Risk Analytics

**Enterprise AI Platform for Real-Time Safety Surveillance, Risk Prediction & Construction Operations**

Every feature in this platform aligns with four core pillars: **Plan → Execute → Monitor → Optimize**.

---

## Quickest start — one command

```bash
python automate.py
```

This sets up a virtual environment, installs dependencies, configures `.env` (asks SQLite vs. MySQL
once), seeds realistic demo data, checks whether Ollama is available, and launches the app at
`http://localhost:8501`. Safe to re-run any time. See [Manual setup](#manual-setup) below if you'd
rather do it step by step, or [Automation script options](#automation-script-options) for flags.

Log in with:
```
Email:    admin@cihub.com
Password: Admin@123
```

---

## What's inside

- **Construction Command Center** — portfolio-wide dashboard: KPIs, progress timeline, budget vs.
  actual, a live AI risk score, an AI-narrated insight, notifications, recent activity, AI recommendations.
- **Project Management** — create/archive projects (new projects get a standard budget breakdown
  auto-created), search & filter, milestones, team assignment, documents, editable status tracking.
- **Client Requirement Analyzer** — turn a client brief into an AI cost estimate, material list,
  suggested timeline, risk level, and Smart Area Planner — with an optional AI-polished summary.
- **Materials & BOQ Generator** — one-click AI material estimation for any project, editable
  usage/availability tracking, and a Bill of Quantities exportable to PDF and Excel.
- **Budget Management** — allocations, expenses, cost trends, and an AI-driven overrun forecast.
- **Workforce Management** — roster, daily attendance, payroll, and AI-suggested headcount by role.
- **Equipment & Inventory** — fleet status and warehouse stock, both **directly editable** (update
  status, fuel, stock levels, reorder thresholds, purchase order status inline), plus maintenance alerts.
- **Safety** — editable PPE/site checklists, an incident log you can resolve inline, emergency contacts.
- **AI Assistant** — a broad, data-grounded chatbot (see below), a composite AI risk analysis with an
  AI-written narrative, an AI recommendation engine with an executive brief, and a delay-risk
  what-if calculator.
- **Analytics & Reports** — portfolio trends and comparisons; Project/Budget/Worker/Inventory/AI
  Summary reports exportable to PDF and Excel, with an AI-generated narrative on the AI Summary Report.
- **Documents** — real file storage (not just metadata) with working downloads and AI-suggested
  categorization on upload.
- **Floating AI chat** — a chat bubble in the bottom-right corner on every page (except AI Assistant,
  which already has the full experience), so you're never more than one click from asking a question.
- **Admin Panel** — user/role management, activity logs, one-click demo data reset.
- **Dark / light theme toggle** — one click, anywhere (sidebar, or the login screen before you're even
  signed in). See [Design system](#design-system--site-blueprint) below.

## The AI Assistant chatbot

The chatbot answers a wide range of real questions by querying your live data directly — no LLM
required for any of these, so it works immediately with zero setup:

- Status & portfolio: *"project status"*, *"how many projects do we have"*, *"which projects are
  delayed / completed / over budget"*, *"tell me about Skyline Financial Tower"*
- Budget: *"remaining budget"*, *"total budget"*, *"which projects are over budget"*
- Materials: *"cement required"*, *"how much steel do we need"*, *"material shortage"*, *"low stock items"*
- Workforce: *"workers today"*, *"how many workers do we have"*
- Risk: *"highest risk project"*, *"what's the risk score"*
- Equipment: *"equipment status"*, *"any equipment overdue for maintenance"*
- Safety: *"safety incidents"*, *"any accidents"*
- Inventory & orders: *"inventory levels"*, *"what needs reorder"*, *"purchase order status"*
- Milestones & documents: *"upcoming milestones"*, *"any deadlines coming up"*, *"how many documents"*

Name a project to scope any question to it (e.g. *"budget for Skyline Tower"*). Only when a question
doesn't match any of the above does it fall through to the local LLM (if connected) or a helpful
fallback message — it never just says "I don't understand."

## Local LLM (Ollama + Gemma 3 1B) — connected across the app

Fully optional, fully local, no API key, no data leaves your machine:

```bash
ollama pull gemma3:1b
ollama serve
```

The app auto-detects it and shows a 🟢 connected badge. Once connected, it enhances (never replaces)
these features with natural-language generation, always grounded in the real numbers already computed:

| Feature | What the LLM adds |
|---|---|
| AI Assistant → Chat | Free-form answers beyond the built-in question patterns above |
| AI Assistant → Risk Analysis | A narrative explanation of *why* a project has its risk score |
| AI Assistant → Recommendations | An executive-brief summary of the recommendation list |
| Dashboard | A one-line AI Insight replacing the static badge |
| Reports → AI Summary Report | A narrative paragraph at the top of the report and its PDF/Excel export |
| Client Requirement Analyzer | A more naturally-phrased AI Summary |
| Documents | AI-suggested category on upload |

Every one of these has a deterministic, correct fallback and a safety check — e.g. the Client
Requirement Analyzer summary is discarded and replaced with the template if the LLM's rewrite doesn't
preserve the exact cost figure; document categorization is validated against a fixed category list
before being trusted. The LLM never gets to invent a number that matters.

## Design system — "Site Blueprint"

A distinctive visual identity built around construction technical drawings rather than a generic
dashboard look: a faint blueprint grid in the background, corner-bracket "registration marks" on
every card, and monospace data readouts for numbers (KPI values, badges). Two themes, one click apart:

- **Dark** — a blueprint laid out on a light table at night (deep navy, blueprint cyan, construction amber).
- **Light** — the same drawing on drafting paper (cream, ink blue, rust amber).

Toggle from the sidebar, or from the login screen before you've even signed in — the whole app,
every chart, every badge, flips instantly because colors are read live rather than hardcoded.

---

## Manual setup

### 1. Prerequisites
- Python 3.10+
- A MySQL 8+ server (or skip this — see "Zero-setup mode" below)

### 2. Install dependencies
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure the database
```bash
cp .env.example .env
```
Edit `.env` with your MySQL credentials, then create the database once:
```sql
CREATE DATABASE cih_db;
```
Tables are created automatically on first run.

**Zero-setup mode:** set `DB_ENGINE=sqlite` in `.env` instead — the app uses a local `cih_local.db`
file with the same schema and features. Swap back to `mysql` any time.

### 4. Load demo data
```bash
python -m database.seed
```
Creates 7 realistic projects across every status, with materials, budgets, workers, equipment, real
downloadable documents, safety records, and 12 weeks of progress history. Safe to re-run — it skips
seeding if data already exists (or use "Reset & Load Demo Data" in the Admin Panel to force a reseed).

### 5. Run
```bash
streamlit run app.py
```

## Automation script options

```bash
python automate.py                # full setup + launch
python automate.py --no-run       # setup only, don't launch Streamlit
python automate.py --reset-data   # wipe and reseed the database before launching
python automate.py --no-venv      # install into the current Python environment instead of a new venv
```

---

## Running the tests

```bash
python -m tests.test_app_smoke        # every screen renders without an exception
python -m tests.test_persistence      # every "add/save/update" action actually persists to the DB
python -m tests.test_new_features     # project creation, AI material generation, document storage
```

All three use Streamlit's `AppTest` harness against a disposable SQLite file — never your real data.
`test_persistence.py` exists specifically because of a real, subtle bug found during development (see
below) — it checks actual database state after every write, not just "did it crash."

---

## Project structure

```
app.py                     # Entry point — auth flow + page router + floating chat widget
automate.py                # One-command setup & launch
config.py                  # Env loading, dual-theme color palettes, business-rule constants
database/
  models.py                # SQLAlchemy ORM schema (every entity in the system)
  db.py                    # Engine/session management
  seed.py                  # Demo data generator (includes real, valid placeholder PDF/XLSX files)
auth/
  auth_utils.py            # Registration, login, password hashing (bcrypt), session guard
ai_engine/
  cost_predictor.py        # RandomForest cost model + budget overrun risk
  material_estimator.py    # Material quantity estimator + Smart Area Planner
  delay_predictor.py       # Schedule-variance delay risk
  workforce_predictor.py   # AI headcount suggestions by role
  risk_analyzer.py         # Composite project risk scoring
  recommendation_engine.py # Actionable recommendations (material/budget/timeline/resource)
  chatbot.py                # Broad rule-based intent matching + local LLM fallback
  llm_client.py              # Ollama (Gemma 3 1B) client — is_available(), chat(), narrate()
  document_ai.py             # AI document category suggestion with heuristic fallback
utils/
  theme.py                   # Theme state — get_colors(), toggle_theme()
  styling.py                  # "Site Blueprint" CSS + KPI cards, badges, section headers
  charts.py                    # Shared theme-aware Plotly styling
  layout.py                     # Sidebar navigation, project selector, theme toggle
  chat_widget.py                 # Shared chat UI (AI Assistant page + floating widget)
  pdf_export.py / excel_export.py  # Report generation, including AI narrative sections
  files.py                          # MIME type detection for real file downloads
screens/                    # One module per page, each exposing a render() function
tests/
  test_app_smoke.py          # Every screen renders without exception
  test_persistence.py         # Every write action actually persists
  test_new_features.py         # New-feature integration checks
```

---

## A note on the AI models

No historical project data exists yet for this system, so the cost, material, delay and workforce
models are bootstrapped from published construction industry thumb rules (see
`config.MATERIAL_THUMB_RULES` and `config.COST_PER_SQFT_BY_QUALITY`) rather than trained on real
outcomes. The cost predictor is a genuine scikit-learn `RandomForestRegressor` — it's just trained
on synthetic examples generated from those thumb rules plus noise, so predictions vary sensibly with
every input instead of being a hardcoded formula.

**The moment you have real historical project data**, retrain `ai_engine/cost_predictor.py` by
swapping the synthetic example generator for a loader over your `projects` table — the model
interface (`predict_cost(...)`) stays the same, so no other code needs to change.

Treat every AI output in this app as a planning baseline, not a guarantee.

## A note on a bug that was found and fixed

During development, a subtle but serious bug was found: `st.rerun()` raises an exception (by design,
so it isn't accidentally caught by user code), and the database session wrapper was treating that as
an error and **rolling back the transaction** — meaning most "add/save" actions across the app looked
successful (no error, page refreshed normally) but silently discarded their own changes. This is fixed
in `database/db.py` (`session_scope` now correctly recognizes Streamlit's own control-flow signals and
commits instead of rolling back), and `tests/test_persistence.py` exists permanently to catch anything
like it in the future by checking actual database state rather than just "no exception was raised."

## Roadmap (not yet built)

Called out in the original spec as future work: AI Floor Plan Generator, Computer Vision progress
detection, Drone Monitoring, BIM Integration, IoT sensor tracking, Digital Twin, OCR for
invoices/drawings, Voice Assistant, native Mobile App, Sustainability tracking.

## Security notes

- Passwords are hashed with bcrypt — never stored in plain text.
- The "Forgot Password" flow resets a password directly after confirming the email exists, which is
  enough for an internal demo. Before any real deployment, gate it behind an emailed one-time code.
- Never commit your real `.env` file — `.env.example` is the template; `.gitignore` already excludes `.env`.
- Uploaded document bytes are stored in the database (MySQL `LONGBLOB` / SQLite `BLOB`) — for very
  large deployments with many large files, consider moving to object storage (S3-compatible) instead;
  the `Document.content` column is the only place that would need to change.
