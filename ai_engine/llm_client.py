"""
Local LLM integration via Ollama, running Gemma 3 1B.

This is entirely optional and entirely local: no API key, no data leaves
the machine, and every function here fails soft (returns None / False)
when Ollama isn't running so the rest of the app behaves exactly as if
this module didn't exist. Callers should always have a non-LLM fallback.

Setup:
    1. Install Ollama:    https://ollama.com/download
    2. Pull the model:    ollama pull gemma3:1b
    3. Start the server:  ollama serve   (usually auto-starts after install)

Config (via .env):
    OLLAMA_ENABLED=true
    OLLAMA_BASE_URL=http://localhost:11434
    OLLAMA_MODEL=gemma3:1b
"""
import json
import time
import logging
import requests
import streamlit as st

from config import OLLAMA_ENABLED, OLLAMA_BASE_URL, OLLAMA_MODEL

_HEALTH_TIMEOUT = 2.0
_CHAT_TIMEOUT = 45
_MAX_RETRIES = 3
_BACKOFF_FACTOR = 1.5

logger = logging.getLogger(__name__)

def _get_ollama_options(temperature: float = 0.0):
    """Returns strict parameters to prevent 1B model hallucinations."""
    return {
        "temperature": temperature,
        "top_p": 0.9,
        "top_k": 40,
        "repeat_penalty": 1.1,
        "num_ctx": 4096,
        "num_predict": 350,
    }


@st.cache_data(ttl=15, show_spinner=False)
def is_available() -> bool:
    """Cheap health check, cached for 15s so we're not hitting Ollama on
    every single Streamlit rerun. Returns False on any error."""
    if not OLLAMA_ENABLED:
        return False
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=_HEALTH_TIMEOUT)
        if r.status_code != 200:
            return False
        installed = [m.get("name", "") for m in r.json().get("models", [])]
        # Ollama tags look like "gemma3:1b" — match the configured model prefix
        return any(name.startswith(OLLAMA_MODEL.split(":")[0]) for name in installed)
    except Exception:
        return False


def chat(messages: list[dict], temperature: float = 0.4) -> str | None:
    """messages: [{"role": "system"|"user"|"assistant", "content": str}, ...]
    Returns the assistant's reply text, or None if the call fails for any
    reason. Includes exponential backoff and retries for production resilience."""
    if not OLLAMA_ENABLED:
        return None
        
    for attempt in range(_MAX_RETRIES):
        try:
            r = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                    "keep_alive": "30m",
                    "options": _get_ollama_options(temperature),
                },
                timeout=_CHAT_TIMEOUT,
            )
            r.raise_for_status()
            content = r.json().get("message", {}).get("content", "").strip()
            
            if content:
                return content
                
            logger.warning(f"Ollama returned empty response (Attempt {attempt+1}/{_MAX_RETRIES})")
            
        except Exception as e:
            logger.error(f"Ollama chat error: {str(e)} (Attempt {attempt+1}/{_MAX_RETRIES})")
            
        if attempt < _MAX_RETRIES - 1:
            time.sleep(_BACKOFF_FACTOR ** attempt)
            
    return None


def chat_stream(messages: list[dict], temperature: float = 0.0):
    """Streams the assistant's reply text chunk by chunk. Yields chunks securely,
    recovers from timeouts and empty streams with exponential backoff retries."""
    if not OLLAMA_ENABLED:
        yield ""
        return
        
    for attempt in range(_MAX_RETRIES):
        try:
            success_chunks = 0
            with requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": True,
                    "keep_alive": "30m",
                    "options": _get_ollama_options(temperature),
                },
                timeout=_CHAT_TIMEOUT,
                stream=True
            ) as r:
                r.raise_for_status()
                for line in r.iter_lines(decode_unicode=True):
                    if line:
                        try:
                            data = json.loads(line)
                            chunk = data.get("message", {}).get("content", "")
                            if chunk:
                                success_chunks += 1
                                yield chunk
                        except json.JSONDecodeError:
                            continue
                            
            if success_chunks > 0:
                return
                
            logger.warning(f"Ollama returned empty stream (Attempt {attempt+1}/{_MAX_RETRIES})")
            
        except requests.exceptions.Timeout:
            logger.error(f"Ollama stream timeout (Attempt {attempt+1}/{_MAX_RETRIES})")
        except Exception as e:
            logger.error(f"Ollama stream error: {str(e)} (Attempt {attempt+1}/{_MAX_RETRIES})")
            
        if attempt < _MAX_RETRIES - 1:
            time.sleep(_BACKOFF_FACTOR ** attempt)
            
    yield "*(The AI assistant is temporarily unavailable. Please try again in a moment.)*"


@st.cache_data(ttl=300, show_spinner=False)
def narrate(system_prompt: str, user_prompt: str, fallback: str, temperature: float = 0.4) -> tuple[str, bool]:
    """The general-purpose entry point every AI-narrative feature in the app
    should use (Dashboard insights, risk explanations, recommendation briefs,
    report summaries...). Returns (text, was_llm_generated) — `fallback` is
    returned whenever Ollama is unavailable or the call fails, so callers
    never need their own try/except around this."""
    if not is_available():
        return fallback, False
    result = chat(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        temperature=temperature,
    )
    if result:
        return result, True
    return fallback, False
