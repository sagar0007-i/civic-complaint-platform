"""Configurable Routing Rules model."""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class RoutingRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Dynamic complaint routing rule based on category, ward/zone, and city."""

    __tablename__ = "routing_rules"

    name = Column(String(150), nullable=False)
    category_id = Column(String(36), ForeignKey("complaint_categories.id"), nullable=False, index=True)
    ward_id = Column(String(36), ForeignKey("wards.id"), nullable=True, index=True)
    city = Column(String(100), nullable=True, index=True)
    target_department_id = Column(String(36), ForeignKey("departments.id"), nullable=False, index=True)
    priority_order = Column(Integer, default=10, nullable=False)  # Lower number = higher priority
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    category = relationship("ComplaintCategory", back_populates="routing_rules")
    ward = relationship("Ward", back_populates="routing_rules")
    target_department = relationship("Department", back_populates="routing_rules")

    __table_args__ = (
        Index("ix_routing_cat_ward", "category_id", "ward_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<RoutingRule('{self.name}', prio={self.priority_order})>"
