"""SQLAlchemy 2.0 Database Engine, Session Management, and Lifecycle."""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, Session
from backend.config import settings
from backend.utils.logging import logger

# Base model for declarative SQLAlchemy models
Base = declarative_base()

# Configure engine parameters
engine_kwargs = {"echo": settings.DB_ECHO}

if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite-specific settings
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL settings
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    engine_kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# Thread-safe scoped session factory with expire_on_commit=False for web/Streamlit stability
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
SessionLocal = scoped_session(session_factory)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for acquiring a clean database session with automatic commit/rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        # Commit if it's a Streamlit control exception (st.rerun, st.stop, st.switch_page)
        exc_name = type(e).__name__
        if exc_name in ("RerunException", "StopException", "ScriptControlException"):
            session.commit()
            raise
        session.rollback()
        logger.error(f"Database session rolled back due to error: {e}")
        raise
    finally:
        session.close()
        SessionLocal.remove()


def init_db() -> None:
    """Initialize database tables from all declared SQLAlchemy models."""
    from backend.models import (
        user,
        department,
        ward,
        category,
        complaint,
        media,
        location,
        history,
        assignment,
        comment,
        routing,
        sla,
        escalation,
        notification,
        audit,
        ai,
    )

    logger.info(f"Initializing database schemas with dialect: {engine.dialect.name}...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")


def check_db_connection() -> bool:
    """Verify active database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
