"""SLA Rules and Escalation models."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class SLARule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """SLA configuration rule defining target response and resolution hours."""

    __tablename__ = "sla_rules"

    name = Column(String(150), nullable=False)
    category_id = Column(String(36), ForeignKey("complaint_categories.id"), nullable=True, index=True)
    severity = Column(String(50), nullable=True, index=True)  # LOW, MEDIUM, HIGH, CRITICAL, or NULL (all)
    response_time_hours = Column(Integer, default=24, nullable=False)  # Time to ACKNOWLEDGE
    resolution_time_hours = Column(Integer, default=72, nullable=False)  # Time to RESOLVE
    escalation_role = Column(String(50), default="DEPARTMENT_ADMIN", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    category = relationship("ComplaintCategory", back_populates="sla_rules")

    def __repr__(self) -> str:
        return f"<SLARule('{self.name}', res_hrs={self.resolution_time_hours})>"


class Escalation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Escalation log when an SLA threshold is breached or manually triggered."""

    __tablename__ = "escalations"

    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    triggered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    reason = Column(String(500), nullable=False)
    escalated_to_role = Column(String(50), default="DEPARTMENT_ADMIN", nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)

    # Relationships
    complaint = relationship("Complaint", back_populates="escalations")

    def __repr__(self) -> str:
        return f"<Escalation(complaint='{self.complaint_id}', reason='{self.reason}')>"
