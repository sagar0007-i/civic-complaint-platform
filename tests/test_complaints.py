"""Complaint Lifecycle & Operations Tests."""

import pytest
from backend.services.complaint_service import ComplaintService
from backend.services.notification_service import NotificationService
from backend.services.sla_service import SLAService
from backend.schemas.complaint import ComplaintCreateSchema, LocationCreateSchema
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


def test_complaint_status_transition_lifecycle(db_session, seed_test_data):
    """Test complaint status transitions through lifecycle and terminal locks."""
    comp_service = ComplaintService(db_session)
    data = seed_test_data

    payload = ComplaintCreateSchema(
        category_id=data["cat_pothole"].id,
        title="Deep Pothole on Linking Road",
        description="Severe road defect causing traffic congestion.",
        severity=ComplaintSeverity.HIGH,
        landmark="Opposite Shopping Mall",
        ward_id=data["ward"].id,
        location=LocationCreateSchema(
            latitude=19.0596,
            longitude=72.8295,
            address="Linking Road",
            city="Mumbai",
        ),
    )

    complaint = comp_service.submit_complaint(
        citizen_id=data["citizen"].id,
        data=payload,
    )

    # 1. Update to IN_PROGRESS
    comp_service.update_status(
        complaint_id=complaint.id,
        user_id=data["officer"].user_id,
        to_status=ComplaintStatus.IN_PROGRESS,
        remarks="Field engineer dispatched to inspect road section.",
    )
    updated = comp_service.get_complaint_by_id(complaint.id)
    assert updated.status == ComplaintStatus.IN_PROGRESS.value
    assert len(updated.status_history) == 2

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

    # 3. Attempting to revert RESOLVED complaint back to IN_PROGRESS must fail
    with pytest.raises(ValueError) as exc_info:
        comp_service.update_status(
            complaint_id=complaint.id,
            user_id=data["officer"].user_id,
            to_status=ComplaintStatus.IN_PROGRESS,
            remarks="Attempting invalid status revert.",
        )
    assert "terminal state" in str(exc_info.value)


def test_complaint_comment_addition(db_session, seed_test_data):
    """Test adding comments to complaint thread."""
    comp_service = ComplaintService(db_session)
    data = seed_test_data

    payload = ComplaintCreateSchema(
        category_id=data["cat_garbage"].id,
        title="Garbage Overflow",
        description="Waste bin overflowing.",
        severity=ComplaintSeverity.LOW,
        ward_id=data["ward"].id,
        location=LocationCreateSchema(
            latitude=19.0596,
            longitude=72.8295,
            address="Main Market",
            city="Mumbai",
        ),
    )

    complaint = comp_service.submit_complaint(
        citizen_id=data["citizen"].id,
        data=payload,
    )

    comp_service.add_comment(
        complaint_id=complaint.id,
        user_id=data["citizen"].id,
        comment_text="When will the repair crew arrive?",
        is_internal=False,
    )
    fetched = comp_service.get_complaint_by_id(complaint.id)
    assert len(fetched.comments) == 1
    assert "repair crew" in fetched.comments[0].comment


def test_user_notifications_read_status(db_session, seed_test_data):
    """Test creating and marking notifications as read."""
    data = seed_test_data
    notif_service = NotificationService(db_session)

    # 1. Create a notification
    notif = notif_service.notif_repo.create(
        user_id=data["citizen"].id,
        title="Test Notification",
        message="This is a test notification.",
    )
    db_session.commit()

    assert notif.is_read is False

    # 2. Mark single notification as read
    notif_service.mark_as_read(notif.id)
    db_session.commit()

    user_notifs = notif_service.get_user_notifications(data["citizen"].id)
    target = next(n for n in user_notifs if n.id == notif.id)
    assert target.is_read is True

    # 3. Mark all as read
    notif_service.mark_all_read(data["citizen"].id)
    db_session.commit()

    unread = [n for n in notif_service.get_user_notifications(data["citizen"].id) if not n.is_read]
    assert len(unread) == 0


def test_public_delay_justification_submission(db_session, seed_test_data):
    """Test public delay justification submission and SLA metadata reporting."""
    comp_service = ComplaintService(db_session)
    sla_service = SLAService(db_session)
    data = seed_test_data

    payload = ComplaintCreateSchema(
        category_id=data["cat_pothole"].id,
        title="Delayed Pothole Resurfacing",
        description="Massive crater obstructing arterial junction.",
        severity=ComplaintSeverity.HIGH,
        ward_id=data["ward"].id,
        location=LocationCreateSchema(
            latitude=19.0760,
            longitude=72.8777,
            address="SV Road Junction",
            city="Mumbai",
        ),
    )

    complaint = comp_service.submit_complaint(
        citizen_id=data["citizen"].id,
        data=payload,
    )
    db_session.commit()

    # Submit official delay justification
    reason = "Utility cable trenching underway by electricity provider. Asphalt hot-mix laying scheduled post clearance."
    updated, err = comp_service.submit_public_delay_justification(
        complaint_id=complaint.id,
        officer_user_id=data["officer"].user_id,
        delay_reason=reason,
        revised_target_days=4,
    )
    db_session.commit()

    assert err is None
    assert updated is not None
    assert updated.delay_reason == reason
    assert updated.delay_justified_by is not None
    assert updated.revised_resolution_target is not None

    # Check SLA service reporting
    sla_report = sla_service.check_sla_status(updated)
    assert sla_report["has_justification"] is True
    assert sla_report["delay_reason"] == reason

