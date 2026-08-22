"""Complaint Status History / Timeline model."""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class ComplaintStatusHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Audit log of status changes and lifecycle timeline."""

    __tablename__ = "complaint_status_history"

    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    changed_by_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    remarks = Column(Text, nullable=True)
    is_internal_note = Column(Boolean, default=False, nullable=False)

    # Relationships
    complaint = relationship("Complaint", back_populates="status_history")
    changed_by = relationship("User")

    __table_args__ = (
        Index("ix_history_complaint_created", "complaint_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<StatusHistory({self.from_status} -> {self.to_status})>"
