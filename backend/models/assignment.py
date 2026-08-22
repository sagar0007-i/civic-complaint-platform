"""Complaint Assignment model."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class ComplaintAssignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Record of officer assignment changes for a complaint."""

    __tablename__ = "complaint_assignments"

    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    officer_id = Column(String(36), ForeignKey("officers.id"), nullable=False, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False, index=True)
    assigned_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    note = Column(Text, nullable=True)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    complaint = relationship("Complaint", back_populates="assignments")
    officer = relationship("Officer", back_populates="assignments")
    assigned_by = relationship("User")

    __table_args__ = (
        Index("ix_assignments_complaint_officer", "complaint_id", "officer_id"),
    )

    def __repr__(self) -> str:
        return f"<ComplaintAssignment(complaint='{self.complaint_id}', officer='{self.officer_id}')>"
