"""Notification model."""

from enum import Enum
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class NotificationChannel(str, Enum):
    """Channels through which notifications can be dispatched."""

    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"


class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Notification item for citizens or officers."""

    __tablename__ = "notifications"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String(50), default=NotificationChannel.IN_APP.value, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="notifications")
    complaint = relationship("Complaint")

    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "is_read"),
    )

    def __repr__(self) -> str:
        return f"<Notification(user='{self.user_id}', read={self.is_read})>"
