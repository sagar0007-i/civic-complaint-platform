"""SLA & Escalation Unit Tests."""

from datetime import datetime, timezone, timedelta
import pytest
from backend.services.sla_service import SLAService
from backend.models.complaint import Complaint, ComplaintStatus


def test_sla_deadline_calculation(db_session, seed_test_data):
    """Test SLA deadline calculation for High severity."""
    sla_service = SLAService(db_session)
    deadline, resp, res = sla_service.calculate_deadline(
        category_id=None,
        severity="HIGH",
    )
    assert resp == 6
    assert res == 24
    assert deadline > datetime.now(timezone.utc)


def test_sla_breach_status_and_escalation(db_session, seed_test_data):
    """Test overdue SLA detection and auto escalation."""
    sla_service = SLAService(db_session)
    data = seed_test_data

    # Overdue complaint
    overdue_complaint = Complaint(
        complaint_number="CIV-2026-999999",
        citizen_id=data["citizen"].id,
        category_id=data["cat_garbage"].id,
        department_id=data["dept_swm"].id,
        title="Overdue garbage issue",
        description="Not resolved within SLA window.",
        status=ComplaintStatus.IN_PROGRESS.value,
        sla_deadline=datetime.now(timezone.utc) - timedelta(hours=5),  # 5 hours overdue
    )
    db_session.add(overdue_complaint)
    db_session.commit()

    sla_info = sla_service.check_sla_status(overdue_complaint)
    assert sla_info["is_breached"] is True
    assert "Overdue" in sla_info["badge"]

    # Test auto escalation
    escalations = sla_service.check_and_escalate_overdue_complaints()
    assert len(escalations) >= 1
    assert overdue_complaint.is_escalated is True


def test_auto_escalation_24h_threshold(db_session, seed_test_data):
    """Test auto-escalation specifically targeting complaints overdue by > 24 hours."""
    sla_service = SLAService(db_session)
    data = seed_test_data

    # Complaint overdue by 30 hours (> 24h)
    comp_overdue_30h = Complaint(
        complaint_number="CIV-2026-888881",
        citizen_id=data["citizen"].id,
        category_id=data["cat_garbage"].id,
        department_id=data["dept_swm"].id,
        title="Severely overdue garbage",
        description="Overdue by 30 hours.",
        status=ComplaintStatus.SUBMITTED.value,
        sla_deadline=datetime.now(timezone.utc) - timedelta(hours=30),
        is_escalated=False,
    )
    # Complaint overdue by only 6 hours (< 24h)
    comp_overdue_6h = Complaint(
        complaint_number="CIV-2026-888882",
        citizen_id=data["citizen"].id,
        category_id=data["cat_garbage"].id,
        department_id=data["dept_swm"].id,
        title="Mildly overdue garbage",
        description="Overdue by 6 hours.",
        status=ComplaintStatus.SUBMITTED.value,
        sla_deadline=datetime.now(timezone.utc) - timedelta(hours=6),
        is_escalated=False,
    )
    db_session.add_all([comp_overdue_30h, comp_overdue_6h])
    db_session.commit()

    # Run auto-escalation with 24h threshold
    escalations_24h = sla_service.check_and_escalate_overdue_complaints(min_overdue_hours=24.0)
    
    # 30h complaint should be escalated, 6h complaint should NOT be escalated
    assert comp_overdue_30h.is_escalated is True
    assert comp_overdue_6h.is_escalated is False
    assert any(e.complaint_id == comp_overdue_30h.id for e in escalations_24h)

    # Calling check_sla_status on 30h complaint shows [🔥 Escalated]
    sla_info = sla_service.check_sla_status(comp_overdue_30h)
    assert sla_info["is_escalated"] is True
    assert "Escalated" in sla_info["badge"]
