"""Complaint Orchestration and Lifecycle Business Logic Service."""

import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.repositories.complaint_repo import ComplaintRepository
from backend.repositories.category_repo import CategoryRepository
from backend.repositories.department_repo import DepartmentRepository
from backend.repositories.ward_repo import WardRepository
from backend.models.complaint import Complaint, ComplaintStatus, ComplaintSeverity
from backend.models.ai import AIClassification
from backend.schemas.complaint import ComplaintCreateSchema, ComplaintStatusUpdateSchema, ComplaintAssignSchema
from backend.services.routing_service import RoutingService
from backend.services.sla_service import SLAService
from backend.services.duplicate_service import DuplicateDetectionService
from backend.services.ai_service import AIService
from backend.services.location_service import LocationService
from backend.services.notification_service import NotificationService
from backend.services.audit_service import AuditService
from backend.services.gov_integration import MockGovernmentIntegrationService
from backend.utils.formatting import generate_complaint_id
from backend.utils.security import sanitize_text
from backend.utils.logging import logger


class ComplaintService:
    """Master service for managing the complete lifecycle of civic complaints."""

    def __init__(self, session: Session):
        self.session = session
        self.complaint_repo = ComplaintRepository(session)
        self.category_repo = CategoryRepository(session)
        self.department_repo = DepartmentRepository(session)
        self.ward_repo = WardRepository(session)

        # Integrated services
        self.routing_service = RoutingService(session)
        self.sla_service = SLAService(session)
        self.duplicate_service = DuplicateDetectionService(session)
        self.ai_service = AIService()
        self.location_service = LocationService()
        self.notification_service = NotificationService(session)
        self.audit_service = AuditService(session)
        self.gov_service = MockGovernmentIntegrationService()

    def submit_complaint(
        self,
        citizen_id: str,
        data: ComplaintCreateSchema,
        ip_address: Optional[str] = None,
    ) -> Complaint:
        """
        Submit a new civic complaint:
        1. Clean & validate inputs
        2. Resolve Ward & Routing
        3. Calculate SLA resolution deadline
        4. Create Complaint and attach Location & Media
        5. Record initial 'SUBMITTED' timeline status
        6. Generate non-blocking AI Classification & Summary
        7. Send in-app Notifications to Citizen & Officer
        8. Send to Mock Government Integration Gateway
        9. Write Immutable Audit Log
        """
        # 1. Sanitize text
        title = sanitize_text(data.title)
        description = sanitize_text(data.description)
        landmark = sanitize_text(data.landmark)

        # 2. Determine Ward (auto-detect nearest ward if not explicitly specified)
        ward_id = data.ward_id
        if not ward_id:
            wards = self.ward_repo.get_all()
            nearest_ward = self.location_service.find_nearest_ward(
                data.location.latitude,
                data.location.longitude,
                wards,
            )
            if nearest_ward:
                ward_id = nearest_ward.id

        # 3. Dynamic Routing Engine
        dept_id, route_reason, assigned_officer_id = self.routing_service.route_complaint(
            category_id=data.category_id,
            ward_id=ward_id,
            city=data.location.city,
        )

        # 4. Calculate SLA Deadline
        sla_deadline, resp_hours, res_hours = self.sla_service.calculate_deadline(
            category_id=data.category_id,
            severity=data.severity.value,
        )

        # 5. Generate Unique Complaint Number
        # Loop with random fallback to ensure uniqueness
        for _ in range(5):
            comp_num = generate_complaint_id()
            if not self.complaint_repo.get_by_number(comp_num):
                break

        # 6. Create Complaint Record
        complaint = self.complaint_repo.create(
            complaint_number=comp_num,
            citizen_id=citizen_id,
            category_id=data.category_id,
            department_id=dept_id,
            title=title,
            description=description,
            severity=data.severity.value,
            status=ComplaintStatus.SUBMITTED.value,
            landmark=landmark,
            ward_id=ward_id,
            assigned_officer_id=assigned_officer_id,
            sla_deadline=sla_deadline,
        )

        # 7. Attach Location
        self.complaint_repo.add_location(
            complaint_id=complaint.id,
            latitude=data.location.latitude,
            longitude=data.location.longitude,
            address=data.location.address,
            landmark=landmark or data.location.landmark,
            accuracy_meters=data.location.accuracy_meters,
            city=data.location.city,
            ward_name=data.location.ward_name,
            pincode=data.location.pincode,
        )

        # 8. Attach Uploaded Media Metadata
        for media_meta in data.media_files:
            self.complaint_repo.add_media(
                complaint_id=complaint.id,
                file_name=media_meta.file_name,
                original_filename=media_meta.original_filename,
                file_size_bytes=media_meta.file_size_bytes,
                mime_type=media_meta.mime_type,
                storage_provider=media_meta.storage_provider,
                storage_path=media_meta.storage_path,
                file_hash=media_meta.file_hash,
                media_type=media_meta.media_type,
                is_public=media_meta.is_public,
            )

        # 9. Record Initial Timeline Status
        self.complaint_repo.add_status_history(
            complaint_id=complaint.id,
            from_status=None,
            to_status=ComplaintStatus.SUBMITTED.value,
            changed_by_id=citizen_id,
            remarks=f"Complaint submitted by citizen. {route_reason}.",
        )

        # 10. AI Suggestions (Classification, Department, Summary)
        try:
            ai_bundle = self.ai_service.get_suggestions(
                title=title,
                description=description,
                landmark=landmark,
            )
            ai_classification = AIClassification(
                complaint_id=complaint.id,
                suggested_severity=ai_bundle.get("suggested_severity"),
                confidence_score=ai_bundle.get("confidence_score"),
                summary_text=ai_bundle.get("summary_text"),
                raw_response=json.dumps(ai_bundle),
            )
            self.session.add(ai_classification)
            self.session.flush()
        except Exception as e:
            logger.warning(f"Non-fatal error generating AI classification: {e}")

        # 11. Dispatch Notifications
        self.notification_service.notify_citizen_status_change(
            complaint=complaint,
            new_status=ComplaintStatus.SUBMITTED.value,
        )

        if assigned_officer_id and complaint.assigned_officer:
            self.notification_service.notify_officer_assignment(
                officer_user_id=complaint.assigned_officer.user_id,
                complaint=complaint,
            )

        # 12. Mock ULB / Municipal Integration
        self.gov_service.forward_complaint_to_ulb(complaint)

        # 13. Audit Log
        self.audit_service.log_event(
            action="COMPLAINT_CREATE",
            entity_type="Complaint",
            entity_id=complaint.id,
            user_id=citizen_id,
            ip_address=ip_address,
            details={
                "complaint_number": complaint.complaint_number,
                "category_id": data.category_id,
                "department_id": dept_id,
                "severity": data.severity.value,
            },
        )

        logger.info(f"Complaint successfully created and routed: {complaint.complaint_number}")
        return complaint

    def get_complaint_by_number(self, complaint_number: str) -> Optional[Complaint]:
        """Fetch complaint by public number."""
        return self.complaint_repo.get_by_number(complaint_number)

    def get_complaint_by_id(self, complaint_id: str) -> Optional[Complaint]:
        """Fetch complaint by UUID."""
        return self.complaint_repo.get_by_id(complaint_id)

    def update_status(
        self,
        complaint_id: str,
        user_id: str,
        to_status: ComplaintStatus,
        remarks: Optional[str] = None,
        is_internal_note: bool = False,
        ip_address: Optional[str] = None,
    ) -> Complaint:
        """Execute a complaint status transition with history and notifications."""
        complaint = self.complaint_repo.get_by_id(complaint_id)
        if not complaint:
            raise ValueError(f"Complaint {complaint_id} not found.")

        from_status = complaint.status
        clean_remarks = sanitize_text(remarks)

        # Update status
        complaint.status = to_status.value
        if to_status == ComplaintStatus.RESOLVED:
            complaint.resolved_at = datetime.now(timezone.utc)

        # Record timeline history
        self.complaint_repo.add_status_history(
            complaint_id=complaint.id,
            from_status=from_status,
            to_status=to_status.value,
            changed_by_id=user_id,
            remarks=clean_remarks,
            is_internal_note=is_internal_note,
        )

        # Notify citizen unless purely internal note
        if not is_internal_note:
            self.notification_service.notify_citizen_status_change(
                complaint=complaint,
                new_status=to_status.value,
                remarks=clean_remarks,
            )

        # Audit log
        self.audit_service.log_event(
            action="COMPLAINT_STATUS_CHANGE",
            entity_type="Complaint",
            entity_id=complaint.id,
            user_id=user_id,
            ip_address=ip_address,
            details={
                "from_status": from_status,
                "to_status": to_status.value,
                "remarks": clean_remarks,
            },
        )

        return complaint

    def assign_to_officer(
        self,
        complaint_id: str,
        officer_id: str,
        assigned_by_id: str,
        note: Optional[str] = None,
    ) -> Complaint:
        """Assign or reassign an officer to a complaint."""
        complaint = self.complaint_repo.get_by_id(complaint_id)
        if not complaint:
            raise ValueError(f"Complaint {complaint_id} not found.")

        assignment = self.complaint_repo.assign_officer(
            complaint_id=complaint.id,
            officer_id=officer_id,
            department_id=complaint.department_id,
            assigned_by_id=assigned_by_id,
            note=sanitize_text(note),
        )

        # Record history
        self.complaint_repo.add_status_history(
            complaint_id=complaint.id,
            from_status=complaint.status,
            to_status=ComplaintStatus.ASSIGNED.value,
            changed_by_id=assigned_by_id,
            remarks=f"Assigned to officer {assignment.officer.designation if assignment.officer else ''} ({assignment.officer.employee_code if assignment.officer else ''}).",
        )

        # Notify officer
        if assignment.officer:
            self.notification_service.notify_officer_assignment(
                officer_user_id=assignment.officer.user_id,
                complaint=complaint,
            )

        return complaint

    def add_comment(
        self,
        complaint_id: str,
        user_id: str,
        comment_text: str,
        is_internal: bool = False,
    ) -> None:
        """Add comment or update to complaint thread."""
        cleaned = sanitize_text(comment_text)
        if not cleaned:
            raise ValueError("Comment cannot be empty.")

        self.complaint_repo.add_comment(
            complaint_id=complaint_id,
            user_id=user_id,
            comment=cleaned,
            is_internal=is_internal,
        )

    def check_for_duplicates(
        self,
        category_id: str,
        latitude: float,
        longitude: float,
        title: str,
        description: str,
    ) -> List[Dict[str, Any]]:
        """Pre-submission duplicate scanner."""
        return self.duplicate_service.find_potential_duplicates(
            category_id=category_id,
            latitude=latitude,
            longitude=longitude,
            title=title,
            description=description,
        )

    def list_complaints(self, **kwargs) -> List[Complaint]:
        """Search and filter complaints."""
        return self.complaint_repo.list_complaints(**kwargs)
