"""Audit Logging model for compliance and security auditing."""

from sqlalchemy import Column, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """System-wide immutable audit trail for security and regulatory compliance."""

    __tablename__ = "audit_logs"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., AUTH_LOGIN, COMPLAINT_CREATE, STATUS_CHANGE
    entity_type = Column(String(100), nullable=False, index=True)  # e.g., Complaint, User, SLARule
    entity_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(50), nullable=True)
    details_json = Column(Text, nullable=True)  # JSON formatted metadata

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_action_created", "action", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(action='{self.action}', entity='{self.entity_type}:{self.entity_id}')>"
