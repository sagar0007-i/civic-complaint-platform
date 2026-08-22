"""AI Classification and Recommendation model."""

from sqlalchemy import Column, String, Text, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class AIClassification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AI suggestions for classification, severity, duplicate analysis, and summary."""

    __tablename__ = "ai_classifications"

    complaint_id = Column(String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    suggested_category_id = Column(String(36), ForeignKey("complaint_categories.id"), nullable=True)
    suggested_severity = Column(String(50), nullable=True)
    suggested_department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    confidence_score = Column(Float, nullable=True)
    duplicate_of_complaint_id = Column(String(36), ForeignKey("complaints.id"), nullable=True)
    summary_text = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)  # Raw model inference response

    # Relationships
    complaint = relationship("Complaint", back_populates="ai_classification", foreign_keys=[complaint_id])
    suggested_category = relationship("ComplaintCategory")
    suggested_department = relationship("Department")
    duplicate_of_complaint = relationship("Complaint", foreign_keys=[duplicate_of_complaint_id])

    def __repr__(self) -> str:
        return f"<AIClassification(complaint='{self.complaint_id}', confidence={self.confidence_score})>"
