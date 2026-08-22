"""Government Department model."""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class Department(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Civic administration department (e.g. Sanitation, Roads, Water, etc.)."""

    __tablename__ = "departments"

    name = Column(String(150), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    officers = relationship("Officer", back_populates="department")
    categories = relationship("ComplaintCategory", back_populates="department")
    complaints = relationship("Complaint", back_populates="department")
    routing_rules = relationship("RoutingRule", back_populates="target_department")

    def __repr__(self) -> str:
        return f"<Department(name='{self.name}', code='{self.code}')>"
