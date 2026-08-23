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


def _auto_migrate_sqlite() -> None:
    """Ensure newly added model columns are added to existing SQLite database tables."""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    try:
        with engine.connect() as conn:
            for table_name, table in Base.metadata.tables.items():
                result = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
                existing_cols = {row[1] for row in result}
                if not existing_cols:
                    continue
                for col in table.columns:
                    if col.name not in existing_cols:
                        col_type = "TEXT"
                        type_str = str(col.type).upper()
                        if "INT" in type_str or "BOOL" in type_str:
                            col_type = "INTEGER"
                        elif "FLOAT" in type_str or "REAL" in type_str:
                            col_type = "REAL"
                        elif "DATE" in type_str or "TIME" in type_str:
                            col_type = "TIMESTAMP"

                        logger.info(f"Auto-migrating SQLite: adding column {table_name}.{col.name} ({col_type})")
                        try:
                            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}"))
                            conn.commit()
                        except Exception as e:
                            logger.warning(f"Could not auto-add column {table_name}.{col.name}: {e}")
    except Exception as err:
        logger.warning(f"SQLite auto-migration check skipped: {err}")


def init_db() -> None:
    """Initialize database tables from all declared SQLAlchemy models and migrate missing columns."""
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
    _auto_migrate_sqlite()
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
