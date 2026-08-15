"""
Engine + session management. Streamlit reruns the whole script on every
interaction, so the engine is cached with st.cache_resource to avoid
reconnecting to MySQL on every click.
"""
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import SQLALCHEMY_DATABASE_URL
from database.models import Base


@st.cache_resource(show_spinner=False)
def get_engine():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    Base.metadata.create_all(engine)
    return engine


def get_session() -> Session:
    """Returns a fresh session bound to the cached engine.
    Callers are responsible for closing it (use as a context manager)."""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return SessionLocal()


try:
    from streamlit.runtime.scriptrunner_utils.exceptions import RerunException, StopException
    _CONTROL_FLOW_EXCEPTIONS = (RerunException, StopException)
except ImportError:
    # Streamlit moved/renamed this internal module in some version — fall
    # back to name-based detection below rather than silently reintroducing
    # the rollback bug this class exists to fix.
    _CONTROL_FLOW_EXCEPTIONS = ()


def _is_streamlit_control_flow(exc_type) -> bool:
    """st.rerun() and st.stop() work by raising an exception that inherits
    from BaseException (deliberately, so ordinary `except Exception` blocks
    in user code don't accidentally swallow it). That means a context
    manager's __exit__ sees a non-None exc_type on every single st.rerun()
    call — treating that as a real error and rolling back would silently
    discard every DB write made just before the rerun, which is exactly
    the bug this function exists to prevent."""
    if exc_type is None:
        return False
    if _CONTROL_FLOW_EXCEPTIONS and issubclass(exc_type, _CONTROL_FLOW_EXCEPTIONS):
        return True
    return exc_type.__name__ in ("RerunException", "StopException")


class session_scope:
    """Context manager: `with session_scope() as db: ...` commits on success
    (including when the block exits via st.rerun()/st.stop()), rolls back on
    a genuine error, and always closes the session."""

    def __enter__(self):
        self.db = get_session()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None or _is_streamlit_control_flow(exc_type):
                self.db.commit()
            else:
                self.db.rollback()
        finally:
            self.db.close()
        return False  # never suppress the exception — let st.rerun()/errors keep propagating
