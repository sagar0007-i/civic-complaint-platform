"""Complaint Repository for database queries and updates."""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload
from backend.models.complaint import Complaint, ComplaintStatus, ComplaintSeverity
from backend.models.location import ComplaintLocation
from backend.models.media import ComplaintMedia
from backend.models.history import ComplaintStatusHistory
from backend.models.assignment import ComplaintAssignment
from backend.models.comment import ComplaintComment
from backend.models.department import Department
from backend.models.category import ComplaintCategory
from backend.models.ward import Ward
from backend.models.user import User, Officer


class ComplaintRepository:
    """Operations for Complaints and associated entities."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, complaint_id: str) -> Optional[Complaint]:
        """Fetch a single complaint by UUID with all related details."""
        return (
            self.session.query(Complaint)
            .options(
                joinedload(Complaint.citizen),
                joinedload(Complaint.category),
                joinedload(Complaint.department),
                joinedload(Complaint.assigned_officer).joinedload(Officer.user),
                joinedload(Complaint.ward),
                joinedload(Complaint.location),
                joinedload(Complaint.media),
                joinedload(Complaint.status_history).joinedload(ComplaintStatusHistory.changed_by),
                joinedload(Complaint.comments).joinedload(ComplaintComment.user),
                joinedload(Complaint.ai_classification),
            )
            .filter(Complaint.id == complaint_id)
            .first()
        )

    def get_by_number(self, complaint_number: str) -> Optional[Complaint]:
        """Fetch a complaint by public human-readable number (e.g. CIV-2026-000042)."""
        return (
            self.session.query(Complaint)
            .options(
                joinedload(Complaint.citizen),
                joinedload(Complaint.category),
                joinedload(Complaint.department),
                joinedload(Complaint.assigned_officer).joinedload(Officer.user),
                joinedload(Complaint.ward),
                joinedload(Complaint.location),
                joinedload(Complaint.media),
                joinedload(Complaint.status_history).joinedload(ComplaintStatusHistory.changed_by),
                joinedload(Complaint.comments).joinedload(ComplaintComment.user),
                joinedload(Complaint.ai_classification),
            )
            .filter(Complaint.complaint_number.ilike(complaint_number.strip()))
            .first()
        )

    def create(
        self,
        complaint_number: str,
        citizen_id: str,
        category_id: str,
        department_id: str,
        title: str,
        description: str,
        severity: str = ComplaintSeverity.MEDIUM.value,
        status: str = ComplaintStatus.SUBMITTED.value,
        landmark: Optional[str] = None,
        ward_id: Optional[str] = None,
        assigned_officer_id: Optional[str] = None,
        sla_deadline: Optional[datetime] = None,
    ) -> Complaint:
        """Create a new Complaint entity."""
        complaint = Complaint(
            complaint_number=complaint_number,
            citizen_id=citizen_id,
            category_id=category_id,
            department_id=department_id,
            assigned_officer_id=assigned_officer_id,
            ward_id=ward_id,
            title=title.strip(),
            description=description.strip(),
            severity=severity,
            status=status,
            landmark=landmark.strip() if landmark else None,
            sla_deadline=sla_deadline,
            is_escalated=False,
        )
        self.session.add(complaint)
        self.session.flush()
        return complaint

    def add_location(
        self,
        complaint_id: str,
        latitude: float,
        longitude: float,
        address: Optional[str] = None,
        landmark: Optional[str] = None,
        accuracy_meters: Optional[float] = None,
        city: str = "Mumbai",
        ward_name: Optional[str] = None,
        pincode: Optional[str] = None,
    ) -> ComplaintLocation:
        """Attach geographic location to a complaint."""
        loc = ComplaintLocation(
            complaint_id=complaint_id,
            latitude=latitude,
            longitude=longitude,
            address=address,
            landmark=landmark,
            accuracy_meters=accuracy_meters,
            city=city,
            ward_name=ward_name,
            pincode=pincode,
        )
        self.session.add(loc)
        self.session.flush()
        return loc

    def add_media(
        self,
        complaint_id: str,
        file_name: str,
        original_filename: str,
        file_size_bytes: int,
        mime_type: str,
        storage_provider: str,
        storage_path: str,
        file_hash: Optional[str] = None,
        media_type: str = "image",
        is_public: bool = True,
    ) -> ComplaintMedia:
        """Attach media file metadata to a complaint."""
        media = ComplaintMedia(
            complaint_id=complaint_id,
            file_name=file_name,
            original_filename=original_filename,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
            storage_provider=storage_provider,
            storage_path=storage_path,
            file_hash=file_hash,
            media_type=media_type,
            is_public=is_public,
        )
        self.session.add(media)
        self.session.flush()
        return media

    def add_status_history(
        self,
        complaint_id: str,
        from_status: Optional[str],
        to_status: str,
        changed_by_id: Optional[str] = None,
        remarks: Optional[str] = None,
        is_internal_note: bool = False,
    ) -> ComplaintStatusHistory:
        """Record status transition in timeline history."""
        history = ComplaintStatusHistory(
            complaint_id=complaint_id,
            from_status=from_status,
            to_status=to_status,
            changed_by_id=changed_by_id,
            remarks=remarks,
            is_internal_note=is_internal_note,
        )
        self.session.add(history)
        self.session.flush()
        self.session.expire_all()
        return history

    def add_comment(
        self,
        complaint_id: str,
        user_id: str,
        comment: str,
        is_internal: bool = False,
    ) -> ComplaintComment:
        """Add citizen or officer remark."""
        c = ComplaintComment(
            complaint_id=complaint_id,
            user_id=user_id,
            comment=comment.strip(),
            is_internal=is_internal,
        )
        self.session.add(c)
        self.session.flush()
        self.session.expire_all()
        return c

    def assign_officer(
        self,
        complaint_id: str,
        officer_id: str,
        department_id: str,
        assigned_by_id: Optional[str] = None,
        note: Optional[str] = None,
    ) -> ComplaintAssignment:
        """Assign officer to complaint."""
        complaint = self.get_by_id(complaint_id)
        if complaint:
            complaint.assigned_officer_id = officer_id
            if complaint.status == ComplaintStatus.SUBMITTED.value:
                complaint.status = ComplaintStatus.ASSIGNED.value

        assignment = ComplaintAssignment(
            complaint_id=complaint_id,
            officer_id=officer_id,
            department_id=department_id,
            assigned_by_id=assigned_by_id,
            note=note,
        )
        self.session.add(assignment)
        self.session.flush()
        return assignment

    def list_complaints(
        self,
        citizen_id: Optional[str] = None,
        department_id: Optional[str] = None,
        assigned_officer_id: Optional[str] = None,
        category_id: Optional[str] = None,
        ward_id: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Complaint]:
        """Search and filter complaints with pagination."""
        query = (
            self.session.query(Complaint)
            .options(
                joinedload(Complaint.citizen),
                joinedload(Complaint.category),
                joinedload(Complaint.department),
                joinedload(Complaint.assigned_officer).joinedload(Officer.user),
                joinedload(Complaint.ward),
                joinedload(Complaint.location),
            )
        )

        if citizen_id:
            query = query.filter(Complaint.citizen_id == citizen_id)
        if department_id:
            query = query.filter(Complaint.department_id == department_id)
        if assigned_officer_id:
            query = query.filter(Complaint.assigned_officer_id == assigned_officer_id)
        if category_id:
            query = query.filter(Complaint.category_id == category_id)
        if ward_id:
            query = query.filter(Complaint.ward_id == ward_id)
        if status:
            query = query.filter(Complaint.status == status)
        if severity:
            query = query.filter(Complaint.severity == severity)

        if search_query:
            term = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    Complaint.complaint_number.ilike(term),
                    Complaint.title.ilike(term),
                    Complaint.description.ilike(term),
                    Complaint.landmark.ilike(term),
                )
            )

        return query.order_by(Complaint.created_at.desc()).limit(limit).offset(offset).all()

    def get_public_stats(self) -> Dict[str, Any]:
        """Aggregate high-level public metrics for transparency."""
        total = self.session.query(func.count(Complaint.id)).scalar() or 0
        resolved = (
            self.session.query(func.count(Complaint.id))
            .filter(Complaint.status == ComplaintStatus.RESOLVED.value)
            .scalar()
            or 0
        )
        in_progress = (
            self.session.query(func.count(Complaint.id))
            .filter(
                Complaint.status.in_(
                    [
                        ComplaintStatus.ACKNOWLEDGED.value,
                        ComplaintStatus.ASSIGNED.value,
                        ComplaintStatus.IN_PROGRESS.value,
                    ]
                )
            )
            .scalar()
            or 0
        )
        escalated = (
            self.session.query(func.count(Complaint.id))
            .filter(Complaint.is_escalated == True)
            .scalar()
            or 0
        )
        return {
            "total_complaints": total,
            "resolved_complaints": resolved,
            "in_progress_complaints": in_progress,
            "escalated_complaints": escalated,
            "resolution_rate_percent": round((resolved / total * 100) if total > 0 else 0, 1),
        }
