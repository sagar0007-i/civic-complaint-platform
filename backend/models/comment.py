"""Complaint Comment model."""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class ComplaintComment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Citizen comments, officer updates, and internal notes on a complaint."""

    __tablename__ = "complaint_comments"

    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    comment = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False, nullable=False)

    # Relationships
    complaint = relationship("Complaint", back_populates="comments")
    user = relationship("User", back_populates="comments")

    __table_args__ = (
        Index("ix_comments_complaint_created", "complaint_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ComplaintComment(id='{self.id}', internal={self.is_internal})>"
