"""Complaint Category model."""

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class ComplaintCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Category of civic complaint (e.g., Garbage, Pothole, Drainage, etc.)."""

    __tablename__ = "complaint_categories"

    name = Column(String(150), unique=True, nullable=False, index=True)
    slug = Column(String(150), unique=True, nullable=False, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False, index=True)
    icon = Column(String(50), default="📌", nullable=False)
    description = Column(String(500), nullable=True)
    default_severity = Column(String(50), default="MEDIUM", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    department = relationship("Department", back_populates="categories")
    complaints = relationship("Complaint", back_populates="category")
    routing_rules = relationship("RoutingRule", back_populates="category")
    sla_rules = relationship("SLARule", back_populates="category")

    def __repr__(self) -> str:
        return f"<ComplaintCategory(name='{self.name}', slug='{self.slug}')>"
