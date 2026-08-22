"""Complaint Location model."""

from sqlalchemy import Column, String, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class ComplaintLocation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Geographic and address location data for a complaint."""

    __tablename__ = "complaint_locations"

    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    address = Column(String(500), nullable=True)
    landmark = Column(String(255), nullable=True)
    accuracy_meters = Column(Float, nullable=True)
    city = Column(String(100), default="Mumbai", nullable=False, index=True)
    ward_name = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True, index=True)

    # Relationships
    complaint = relationship("Complaint", back_populates="location")

    __table_args__ = (
        Index("ix_locations_lat_long", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return f"<ComplaintLocation(lat={self.latitude}, lng={self.longitude}, city='{self.city}')>"
