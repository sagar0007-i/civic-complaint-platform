"""Duplicate Grievance Detection Unit Tests."""

from datetime import datetime, timezone, timedelta
import pytest
from backend.services.duplicate_service import DuplicateDetectionService
from backend.models.complaint import Complaint, ComplaintStatus
from backend.models.location import ComplaintLocation


def test_duplicate_detection_within_proximity(db_session, seed_test_data):
    """Test duplicate detection finds nearby matching complaints."""
    dup_service = DuplicateDetectionService(db_session)
    data = seed_test_data

    # Existing complaint
    c_orig = Complaint(
        complaint_number="CIV-2026-111111",
        citizen_id=data["citizen"].id,
        category_id=data["cat_garbage"].id,
        department_id=data["dept_swm"].id,
        title="Overflowing waste bin near metro",
        description="Garbage bin is full and spreading on the pavement.",
        status=ComplaintStatus.SUBMITTED.value,
        created_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    db_session.add(c_orig)
    db_session.flush()

    loc = ComplaintLocation(
        complaint_id=c_orig.id,
        latitude=12.9784,
        longitude=77.6408,
        address="100 Feet Road, Indiranagar",
    )
    db_session.add(loc)
    db_session.commit()

    # New complaint reported 30 meters away with same topic
    duplicates = dup_service.find_potential_duplicates(
        category_id=data["cat_garbage"].id,
        latitude=12.9786,
        longitude=77.6409,
        title="Dustbin overflow near metro station",
        description="Massive garbage dump overflowing onto the road.",
    )

    assert len(duplicates) >= 1
    assert duplicates[0]["complaint_number"] == "CIV-2026-111111"
    assert duplicates[0]["distance_meters"] < 50
    assert duplicates[0]["similarity_score"] >= 0.50
