"""Complaint Media metadata model."""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class ComplaintMedia(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Metadata for uploaded complaint photos and videos."""

    __tablename__ = "complaint_media"

    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    storage_provider = Column(String(50), default="local", nullable=False)  # local, s3, r2, supabase
    storage_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash
    media_type = Column(String(20), default="image", nullable=False)  # image or video
    is_public = Column(Boolean, default=True, nullable=False)

    # Relationships
    complaint = relationship("Complaint", back_populates="media")

    __table_args__ = (
        Index("ix_media_complaint_type", "complaint_id", "media_type"),
    )

    def __repr__(self) -> str:
        return f"<ComplaintMedia(id='{self.id}', filename='{self.file_name}', mime='{self.mime_type}')>"
