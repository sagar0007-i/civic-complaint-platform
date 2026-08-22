"""All SQLAlchemy 2.0 Database Models."""

from backend.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin
from backend.models.user import User, Officer, UserRole
from backend.models.department import Department
from backend.models.ward import Ward
from backend.models.category import ComplaintCategory
from backend.models.complaint import Complaint, ComplaintStatus, ComplaintSeverity
from backend.models.media import ComplaintMedia
from backend.models.location import ComplaintLocation
from backend.models.history import ComplaintStatusHistory
from backend.models.assignment import ComplaintAssignment
from backend.models.comment import ComplaintComment
from backend.models.routing import RoutingRule
from backend.models.sla import SLARule, Escalation
from backend.models.notification import Notification, NotificationChannel
from backend.models.audit import AuditLog
from backend.models.ai import AIClassification

__all__ = [
    "Base",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "User",
    "Officer",
    "UserRole",
    "Department",
    "Ward",
    "ComplaintCategory",
    "Complaint",
    "ComplaintStatus",
    "ComplaintSeverity",
    "ComplaintMedia",
    "ComplaintLocation",
    "ComplaintStatusHistory",
    "ComplaintAssignment",
    "ComplaintComment",
    "RoutingRule",
    "SLARule",
    "Escalation",
    "Notification",
    "NotificationChannel",
    "AuditLog",
    "AIClassification",
]
