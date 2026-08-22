"""Base model and mixins for SQLAlchemy models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String
from backend.database import Base


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class UUIDPrimaryKeyMixin:
    """Provides a UUID string primary key compatible with both SQLite and PostgreSQL."""

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
        nullable=False,
    )


class TimestampMixin:
    """Provides created_at and updated_at UTC timestamps."""

    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
