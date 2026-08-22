"""Administrative Ward / Zone / Locality model."""

from sqlalchemy import Column, String, Integer, Float, Boolean, Index
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class Ward(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Geographic and administrative municipal ward/zone."""

    __tablename__ = "wards"

    name = Column(String(150), nullable=False, index=True)
    ward_number = Column(Integer, nullable=True, index=True)
    zone = Column(String(100), nullable=False, index=True)  # e.g., Western Suburbs, South Mumbai
    city = Column(String(100), nullable=False, default="Mumbai", index=True)
    state = Column(String(100), nullable=False, default="Maharashtra")
    pincode = Column(String(10), nullable=True, index=True)
    center_latitude = Column(Float, nullable=True)
    center_longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    officers = relationship("Officer", back_populates="ward")
    complaints = relationship("Complaint", back_populates="ward")
    routing_rules = relationship("RoutingRule", back_populates="ward")

    __table_args__ = (
        Index("ix_wards_city_zone", "city", "zone"),
    )

    def __repr__(self) -> str:
        return f"<Ward(name='{self.name}', ward_no={self.ward_number}, zone='{self.zone}')>"
