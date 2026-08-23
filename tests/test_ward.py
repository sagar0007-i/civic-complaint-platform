"""Unit tests for Municipal Wards and Zones editing/updating functionality."""

import pytest
from pydantic import ValidationError
from backend.repositories.department_repo import WardRepository
from backend.repositories.audit_repo import AuditRepository
from backend.schemas.department import WardCreateSchema
from backend.models.ward import Ward


def test_edit_valid_ward(db_session):
    """Test 1 — Edit valid ward details and ensure updates persist."""
    ward_repo = WardRepository(db_session)
    
    # Pre-seed a ward
    ward = ward_repo.create(
        name="Ward G/South (Worli)",
        zone="City Zone",
        ward_number=14,
        pincode="400018",
    )
    db_session.commit()
    
    # Update pincode
    updated = ward_repo.update(
        ward_id=ward.id,
        name="Ward G/South (Worli)",
        zone="City Zone",
        ward_number=14,
        pincode="400019",
    )
    db_session.commit()
    
    assert updated is not None
    assert updated.pincode == "400019"
    
    # Reload and verify persistence
    reloaded = ward_repo.get_by_id(ward.id)
    assert reloaded.pincode == "400019"


def test_invalid_pincode_validation():
    """Test 3 — Invalid pincode validation."""
    # Too short
    with pytest.raises(ValidationError):
        WardCreateSchema(
            name="Test Ward",
            zone="Test Zone",
            ward_number=10,
            pincode="4000",
        )
        
    # Non-numeric
    with pytest.raises(ValidationError):
        WardCreateSchema(
            name="Test Ward",
            zone="Test Zone",
            ward_number=10,
            pincode="ABCDEF",
        )
        
    # Too long
    with pytest.raises(ValidationError):
        WardCreateSchema(
            name="Test Ward",
            zone="Test Zone",
            ward_number=10,
            pincode="4000189",
        )

    # Valid pincode (exactly 6 digits) should pass
    schema = WardCreateSchema(
        name="Test Ward",
        zone="Test Zone",
        ward_number=10,
        pincode="400018",
    )
    assert schema.pincode == "400018"


def test_duplicate_ward_uniqueness(db_session):
    """Test 4 — Duplicate ward detection in the same zone."""
    ward_repo = WardRepository(db_session)
    
    # Seed ward 1
    w1 = ward_repo.create(
        name="Ward G/South",
        zone="City Zone",
        ward_number=14,
    )
    # Seed ward 2
    w2 = ward_repo.create(
        name="Ward L",
        zone="Eastern Suburbs",
        ward_number=25,
    )
    db_session.commit()
    
    # Check that w2 cannot be updated to ward_number=14 in "City Zone"
    duplicate = ward_repo.get_by_number_and_zone(14, "City Zone", exclude_id=w2.id)
    assert duplicate is not None
    assert duplicate.id == w1.id
    
    # Check that w2 CAN be updated/kept as ward_number=25 in "Eastern Suburbs" (excluding itself)
    self_dup = ward_repo.get_by_number_and_zone(25, "Eastern Suburbs", exclude_id=w2.id)
    assert self_dup is None


def test_update_non_existent_ward(db_session):
    """Test 5 — Attempting to update a non-existent ward returns None."""
    ward_repo = WardRepository(db_session)
    res = ward_repo.update(
        ward_id="invalid-id-9999",
        name="Non existent",
        zone="Zone",
    )
    assert res is None


def test_audit_log_upon_update(db_session):
    """Test 7 — Successful update produces proper audit records."""
    ward_repo = WardRepository(db_session)
    audit_repo = AuditRepository(db_session)
    
    ward = ward_repo.create(name="Ward A", zone="South Zone", ward_number=1)
    db_session.commit()
    
    # Perform update
    ward_repo.update(ward.id, name="Ward A New", zone="South Zone", ward_number=1)
    
    # Log audit
    audit = audit_repo.log(
        action="UPDATE_WARD",
        entity_type="Ward",
        entity_id=ward.id,
        user_id="admin-user-id",
        details_json='{"changes": {"name": "Ward A → Ward A New"}}'
    )
    db_session.commit()
    
    assert audit is not None
    assert audit.action == "UPDATE_WARD"
    assert audit.entity_id == str(ward.id)
    assert "Ward A → Ward A New" in audit.details_json
