"""Complaint Lifecycle & Operations Tests."""

import pytest
from backend.services.complaint_service import ComplaintService
from backend.schemas.complaint import ComplaintCreateSchema, LocationCreateSchema, MediaUploadMetaSchema
from backend.models.complaint import ComplaintSeverity, ComplaintStatus


def test_complaint_submission_and_id_format(db_session, seed_test_data):
    """Test full complaint creation pipeline and ID format."""
    comp_service = ComplaintService(db_session)
    data = seed_test_data

    payload = ComplaintCreateSchema(
        category_id=data["cat_garbage"].id,
        title="Uncollected garbage near bus stand",
        description="Piles of solid waste left unattended for over 48 hours.",
        severity=ComplaintSeverity.MEDIUM,
        landmark="Near Central Bus Stand",
        ward_id=data["ward"].id,
        location=LocationCreateSchema(
            latitude=19.0596,
            longitude=72.8295,
            address="Hill Road, Bandra West",
            city="Mumbai",
        ),
        media_files=[],
    )

    complaint = comp_service.submit_complaint(
        citizen_id=data["citizen"].id,
        data=payload,
    )

    assert complaint is not None
    assert complaint.complaint_number.startswith("CIV-2026-")
    assert complaint.status == ComplaintStatus.SUBMITTED.value
    assert complaint.department_id == data["dept_swm"].id
    assert complaint.location is not None
    assert complaint.location.latitude == 19.0596
    assert len(complaint.status_history) == 1
    assert complaint.status_history[0].to_status == ComplaintStatus.SUBMITTED.value


def test_complaint_status_transition_lifecycle(db_session, seed_test_data):
    """Test status updates and audit timeline generation."""
    comp_service = ComplaintService(db_session)
    data = seed_test_data

    payload = ComplaintCreateSchema(
        category_id=data["cat_pothole"].id,
        title="Severe pothole on cross road",
        description="Deep crater damaging two-wheelers.",
        severity=ComplaintSeverity.HIGH,
        location=LocationCreateSchema(
            latitude=19.0590,
            longitude=72.8290,
            address="Linking Road, Bandra West",
            city="Mumbai",
        ),
    )

    complaint = comp_service.submit_complaint(citizen_id=data["citizen"].id, data=payload)

    # 1. Update to IN_PROGRESS
    comp_service.update_status(
        complaint_id=complaint.id,
        user_id=data["officer"].user_id,
        to_status=ComplaintStatus.IN_PROGRESS,
        remarks="Field team deployed with repair vehicle.",
    )
    assert complaint.status == ComplaintStatus.IN_PROGRESS.value

    # 2. Update to RESOLVED
    comp_service.update_status(
        complaint_id=complaint.id,
        user_id=data["officer"].user_id,
        to_status=ComplaintStatus.RESOLVED,
        remarks="Pothole filled and sealed with asphalt.",
    )
    updated = comp_service.get_complaint_by_id(complaint.id)
    assert updated.status == ComplaintStatus.RESOLVED.value
    assert updated.resolved_at is not None
    assert len(updated.status_history) == 3


def test_complaint_comment_addition(db_session, seed_test_data):
    """Test adding comments to complaint thread."""
    comp_service = ComplaintService(db_session)
    data = seed_test_data

    payload = ComplaintCreateSchema(
        category_id=data["cat_garbage"].id,
        title="Overflowing dustbin",
        description="Trash overflowing on road.",
        location=LocationCreateSchema(latitude=12.9780, longitude=77.6400),
    )
    complaint = comp_service.submit_complaint(citizen_id=data["citizen"].id, data=payload)

    comp_service.add_comment(
        complaint_id=complaint.id,
        user_id=data["citizen"].id,
        comment_text="Garbage truck visited but missed the inner street.",
        is_internal=False,
    )

    fetched = comp_service.get_complaint_by_id(complaint.id)
    assert len(fetched.comments) == 1
    assert "missed the inner street" in fetched.comments[0].comment
