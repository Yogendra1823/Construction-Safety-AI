#!/usr/bin/env python3
"""
Construction Intelligence Hub — one-command setup & launch.

Run:  python automate.py

Handles everything needed to go from a fresh clone to a running app:
  1. Checks the Python version
  2. Creates/reuses a virtual environment and installs dependencies
  3. Creates .env from .env.example if missing (asks MySQL vs. SQLite once)
  4. Seeds demo data if the database is empty
  5. Checks whether Ollama + Gemma 3 1B are available and tells you what's
     missing, without blocking the app from starting either way
  6. Launches `streamlit run app.py`

Safe to re-run any time — every step is idempotent and skips work that's
already done. Flags:
  --no-venv     install into the current Python environment instead
  --reset-data  wipe and reseed the database before launching
  --no-run      do setup only, don't launch Streamlit
"""
import os
import platform
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / "venv"
IS_WINDOWS = platform.system() == "Windows"
VENV_PYTHON = VENV_DIR / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")

RESET_DATA = "--reset-data" in sys.argv
NO_VENV = "--no-venv" in sys.argv
NO_RUN = "--no-run" in sys.argv


def _c(text, code):
    if os.environ.get("NO_COLOR") or IS_WINDOWS and "WT_SESSION" not in os.environ:
        return text
    return f"\033[{code}m{text}\033[0m"


def step(msg):
    print(f"\n{_c('▶', '36')} {_c(msg, '1')}")


def ok(msg):
    print(f"  {_c('✓', '32')} {msg}")


def warn(msg):
    print(f"  {_c('!', '33')} {msg}")


def fail(msg):
    print(f"  {_c('✗', '31')} {msg}")


def run(cmd, **kwargs):
    return subprocess.run(cmd, cwd=ROOT, **kwargs)


def check_python_version():
    step("Checking Python version")
    if sys.version_info < (3, 10):
        fail(f"Python 3.10+ required, found {platform.python_version()}. Please upgrade Python.")
        sys.exit(1)
    ok(f"Python {platform.python_version()}")


def setup_venv():
    if NO_VENV:
        return sys.executable
    step("Setting up virtual environment")
    if VENV_PYTHON.exists():
        ok(f"Reusing existing venv at {VENV_DIR}")
    else:
        print("  Creating venv (this only happens once)...")
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)
        ok("Created venv")
    return str(VENV_PYTHON)


def install_requirements(python_bin):
    step("Installing dependencies")
    result = run([python_bin, "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    result = run([python_bin, "-m", "pip", "install", "--quiet", "-r", "requirements.txt"])
    if result.returncode != 0:
        fail("pip install failed — see output above.")
        sys.exit(1)
    ok("All dependencies installed")


def setup_env_file():
    step("Configuring environment")
    env_path = ROOT / ".env"
    example_path = ROOT / ".env.example"
    if env_path.exists():
        ok(".env already exists — leaving it as-is")
        return

    print("  No .env found. Choose a database for this run:")
    print("    [1] SQLite  — zero setup, works immediately (recommended for a demo)")
    print("    [2] MySQL   — production-style, requires a running MySQL server")
    choice = input("  Choice [1]: ").strip() or "1"

    content = example_path.read_text()
    if choice == "1":
        content = content.replace("DB_ENGINE=mysql", "DB_ENGINE=sqlite")
        ok("Using SQLite (cih_local.db)")
    else:
        ok("Using MySQL — make sure your server is running and .env credentials are correct")

    import secrets
    content = content.replace(
        "SECRET_KEY=replace-with-a-long-random-string",
        f"SECRET_KEY={secrets.token_hex(32)}",
    )
    env_path.write_text(content)
    ok("Created .env")

    if choice == "2":
        warn("Edit .env with your MySQL credentials before continuing, then re-run this script.")
        print(f"\n  {_c('CREATE DATABASE cih_db;', '2')}  ← run this in MySQL once, tables are created automatically.")


def seed_database(python_bin):
    step("Checking demo data")
    if RESET_DATA:
        result = run([python_bin, "-c",
                      "from database.seed import seed_demo_data; print(seed_demo_data(force=True)[1])"])
    else:
        result = run([python_bin, "-c",
                      "from database.seed import seed_demo_data; print(seed_demo_data()[1])"])
    if result.returncode != 0:
        fail("Could not seed the database — check your DB connection in .env.")
        sys.exit(1)
    ok("Demo data ready")


def check_ollama():
    step("Checking for local AI (Ollama + Gemma 3 1B)")
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as r:
            import json
            models = [m.get("name", "") for m in json.load(r).get("models", [])]
            if any(m.startswith("gemma3") for m in models):
                ok("Ollama is running with gemma3:1b — AI chat and narratives are fully enabled")
                return
            warn("Ollama is running, but gemma3:1b isn't pulled yet.")
            print(f"     Run: {_c('ollama pull gemma3:1b', '2')}")
            return
    except Exception:
        pass
    warn("Ollama isn't running — the app works fully without it (rule-based AI answers everywhere),")
    print(f"     but for the full local-LLM experience: install from {_c('https://ollama.com', '2')},")
    print(f"     then run {_c('ollama pull gemma3:1b', '2')} and {_c('ollama serve', '2')}.")


def launch(python_bin):
    if NO_RUN:
        step("Setup complete — skipping launch (--no-run)")
        return
    step("Launching Construction Intelligence Hub")
    ok("Opening at http://localhost:8501 — press Ctrl+C to stop")
    print()
    run([python_bin, "-m", "streamlit", "run", "app.py"])


def main():
    print(_c("Construction Intelligence Hub — automated setup", "1;36"))
    check_python_version()
    python_bin = setup_venv()
    install_requirements(python_bin)
    setup_env_file()
    seed_database(python_bin)
    check_ollama()
    launch(python_bin)


if __name__ == "__main__":
    main()
