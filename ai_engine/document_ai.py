"""
AI document categorization. A small, low-risk use of the local LLM: suggest
which category a newly-uploaded file probably belongs to, based on its
filename. Always validated against a fixed allow-list before being trusted —
if Gemma returns anything outside that list (or isn't running), we fall back
to a deterministic filename/extension heuristic instead.
"""
from ai_engine import llm_client

DOCUMENT_CATEGORIES = [
    "Structural Drawing", "Contract", "Financial Report", "Safety Document",
    "Site Photo", "Permit", "Material Order", "Other",
]

_EXTENSION_FALLBACK = {
    "jpg": "Site Photo", "jpeg": "Site Photo", "png": "Site Photo", "heic": "Site Photo",
    "xlsx": "Financial Report", "xls": "Financial Report", "csv": "Financial Report",
    "docx": "Contract", "doc": "Contract",
}

_KEYWORD_FALLBACK = [
    ("contract", "Contract"), ("agreement", "Contract"),
    ("safety", "Safety Document"), ("incident", "Safety Document"), ("ppe", "Safety Document"),
    ("permit", "Permit"), ("license", "Permit"), ("approval", "Permit"),
    ("drawing", "Structural Drawing"), ("blueprint", "Structural Drawing"), ("plan", "Structural Drawing"),
    ("budget", "Financial Report"), ("invoice", "Financial Report"), ("cost", "Financial Report"),
    ("order", "Material Order"), ("po_", "Material Order"), ("purchase", "Material Order"),
    ("photo", "Site Photo"), ("site_", "Site Photo"),
]


def _heuristic_category(filename: str) -> str:
    lower = filename.lower()
    for keyword, category in _KEYWORD_FALLBACK:
        if keyword in lower:
            return category
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXTENSION_FALLBACK.get(ext, "Other")


def suggest_category(filename: str) -> tuple[str, bool]:
    """Returns (category, was_ai_suggested). Always returns something valid
    from DOCUMENT_CATEGORIES — never raises, never blocks an upload."""
    fallback = _heuristic_category(filename)

    if not llm_client.is_available():
        return fallback, False

    system = (
        "Classify a construction-project document by its filename into exactly "
        "one of these categories: " + ", ".join(DOCUMENT_CATEGORIES) + ". "
        "Reply with ONLY the category name, exactly as written, nothing else."
    )
    result = llm_client.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": filename}],
        temperature=0.1,
    )
    if result and result.strip() in DOCUMENT_CATEGORIES:
        return result.strip(), True
    return fallback, False
