"""Complaint model and Status/Severity Enums."""

from enum import Enum
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class ComplaintStatus(str, Enum):
    """Lifecycle statuses for a civic complaint."""

    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_INFORMATION = "WAITING_FOR_INFORMATION"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
    REOPENED = "REOPENED"


class ComplaintSeverity(str, Enum):
    """Urgency / Severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Complaint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Core Civic Complaint entity."""

    __tablename__ = "complaints"

    # Unique human-readable complaint identifier (e.g. CIV-2026-000001)
    complaint_number = Column(String(50), unique=True, nullable=False, index=True)

    citizen_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("complaint_categories.id"), nullable=False, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False, index=True)
    assigned_officer_id = Column(String(36), ForeignKey("officers.id"), nullable=True, index=True)
    ward_id = Column(String(36), ForeignKey("wards.id"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), default=ComplaintSeverity.MEDIUM.value, nullable=False, index=True)
    status = Column(String(50), default=ComplaintStatus.SUBMITTED.value, nullable=False, index=True)
    landmark = Column(String(255), nullable=True)

    # SLA tracking & Public Delay Accountability
    sla_deadline = Column(DateTime, nullable=True, index=True)
    is_escalated = Column(Boolean, default=False, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    delay_reason = Column(Text, nullable=True)
    delay_justified_at = Column(DateTime, nullable=True)
    delay_justified_by = Column(String(255), nullable=True)
    revised_resolution_target = Column(DateTime, nullable=True)

    # Relationships
    citizen = relationship("User", back_populates="complaints", foreign_keys=[citizen_id])
    category = relationship("ComplaintCategory", back_populates="complaints")
    department = relationship("Department", back_populates="complaints")
    assigned_officer = relationship("Officer", back_populates="assigned_complaints", foreign_keys=[assigned_officer_id])
    ward = relationship("Ward", back_populates="complaints")

    location = relationship("ComplaintLocation", back_populates="complaint", uselist=False, cascade="all, delete-orphan")
    media = relationship("ComplaintMedia", back_populates="complaint", cascade="all, delete-orphan")
    status_history = relationship(
        "ComplaintStatusHistory",
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="ComplaintStatusHistory.created_at.asc()",
    )
    assignments = relationship(
        "ComplaintAssignment",
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="ComplaintAssignment.assigned_at.desc()",
    )
    comments = relationship(
        "ComplaintComment",
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="ComplaintComment.created_at.asc()",
    )
    ai_classification = relationship(
        "AIClassification",
        back_populates="complaint",
        foreign_keys="AIClassification.complaint_id",
        uselist=False,
        cascade="all, delete-orphan",
    )
    escalations = relationship("Escalation", back_populates="complaint", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_complaints_dept_status", "department_id", "status"),
        Index("ix_complaints_created_status", "created_at", "status"),
        Index("ix_complaints_ward_category", "ward_id", "category_id"),
    )

    def __repr__(self) -> str:
        return f"<Complaint(number='{self.complaint_number}', status='{self.status}')>"
