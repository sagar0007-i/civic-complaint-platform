"""User, Roles, and Officer Profiles models."""

from enum import Enum
from sqlalchemy import Column, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class UserRole(str, Enum):
    """User Roles for RBAC."""

    CITIZEN = "CITIZEN"
    OFFICER = "OFFICER"
    DEPARTMENT_ADMIN = "DEPARTMENT_ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """System user account."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.CITIZEN.value, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    officer_profile = relationship("Officer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    complaints = relationship("Complaint", back_populates="citizen", foreign_keys="Complaint.citizen_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    comments = relationship("ComplaintComment", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(email='{self.email}', role='{self.role}')>"


class Officer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Government officer profile linked to a user account."""

    __tablename__ = "officers"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False, index=True)
    ward_id = Column(String(36), ForeignKey("wards.id"), nullable=True, index=True)
    designation = Column(String(100), nullable=False, default="Junior Engineer")
    employee_code = Column(String(50), unique=True, nullable=False, index=True)
    is_available = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="officer_profile")
    department = relationship("Department", back_populates="officers")
    ward = relationship("Ward", back_populates="officers")
    assigned_complaints = relationship("Complaint", back_populates="assigned_officer", foreign_keys="Complaint.assigned_officer_id")
    assignments = relationship("ComplaintAssignment", back_populates="officer")

    __table_args__ = (
        Index("ix_officers_dept_ward", "department_id", "ward_id"),
    )

    def __repr__(self) -> str:
        return f"<Officer(code='{self.employee_code}', designation='{self.designation}')>"
