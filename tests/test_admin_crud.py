"""Unit tests for the remaining System Admin Console CRUD edit/update features."""

import pytest
from pydantic import ValidationError
from backend.repositories.department_repo import DepartmentRepository
from backend.repositories.category_repo import CategoryRepository
from backend.repositories.routing_repo import RoutingRepository
from backend.repositories.sla_repo import SLARepository
from backend.repositories.user_repo import UserRepository
from backend.repositories.audit_repo import AuditRepository
from backend.models.user import UserRole
from backend.schemas.department import DepartmentCreateSchema, CategoryCreateSchema


def test_edit_department(db_session):
    """Test editing a department and code uniqueness constraints."""
    dept_repo = DepartmentRepository(db_session)
    
    # Pre-seed department 1
    d1 = dept_repo.create(name="Health & Sanitation", code="DEPT_HEALTH")
    # Pre-seed department 2
    d2 = dept_repo.create(name="Roads & Bridges", code="DEPT_ROADS")
    db_session.commit()
    
    # 1. Edit department successfully
    updated = dept_repo.update(d1.id, name="Health Department", code="DEPT_HEALTH_NEW")
    assert updated is not None
    assert updated.name == "Health Department"
    assert updated.code == "DEPT_HEALTH_NEW"
    
    # 2. Duplicate code check
    duplicate = dept_repo.get_by_code_exclude("DEPT_ROADS", exclude_id=d1.id)
    assert duplicate is not None
    assert duplicate.id == d2.id
    
    self_code = dept_repo.get_by_code_exclude("DEPT_HEALTH_NEW", exclude_id=d1.id)
    assert self_code is None


def test_edit_category(db_session):
    """Test editing a category and slug uniqueness constraints."""
    dept_repo = DepartmentRepository(db_session)
    cat_repo = CategoryRepository(db_session)
    
    d1 = dept_repo.create(name="Sanitation", code="DEPT_SWM")
    c1 = cat_repo.create(name="Garbage Pile", slug="garbage-pile", department_id=d1.id)
    c2 = cat_repo.create(name="Pothole Repair", slug="pothole", department_id=d1.id)
    db_session.commit()
    
    # 1. Edit category successfully
    updated = cat_repo.update(c1.id, name="Garbage Clearance", slug="garbage-clear", department_id=d1.id)
    assert updated is not None
    assert updated.name == "Garbage Clearance"
    assert updated.slug == "garbage-clear"
    
    # 2. Slug validation
    with pytest.raises(ValidationError):
        CategoryCreateSchema(name="Too Short Slug", slug="a", department_id=d1.id)
        
    # 3. Duplicate check
    duplicate = cat_repo.get_by_slug_exclude("pothole", exclude_id=c1.id)
    assert duplicate is not None
    assert duplicate.id == c2.id


def test_edit_routing_rule(db_session):
    """Test editing a routing rule."""
    dept_repo = DepartmentRepository(db_session)
    cat_repo = CategoryRepository(db_session)
    routing_repo = RoutingRepository(db_session)
    
    d1 = dept_repo.create(name="Sanitation", code="DEPT_SWM")
    c1 = cat_repo.create(name="Garbage Pile", slug="garbage-pile", department_id=d1.id)
    
    rule = routing_repo.create(name="Route Garbage", category_id=c1.id, target_department_id=d1.id, priority_order=10)
    db_session.commit()
    
    # Edit routing rule
    updated = routing_repo.update(
        rule_id=rule.id,
        name="Route Garbage New",
        category_id=c1.id,
        target_department_id=d1.id,
        priority_order=20,
        is_active=False
    )
    assert updated is not None
    assert updated.name == "Route Garbage New"
    assert updated.priority_order == 20
    assert updated.is_active is False


def test_edit_sla_rule(db_session):
    """Test editing an SLA rule."""
    sla_repo = SLARepository(db_session)
    
    rule = sla_repo.create(name="Standard SLA", severity="HIGH", response_time_hours=4, resolution_time_hours=24)
    db_session.commit()
    
    # Edit SLA rule
    updated = sla_repo.update(
        sla_id=rule.id,
        name="Updated High Priority SLA",
        severity="HIGH",
        response_time_hours=2,
        resolution_time_hours=12,
        escalation_role="SUPER_ADMIN",
        is_active=True
    )
    assert updated is not None
    assert updated.name == "Updated High Priority SLA"
    assert updated.response_time_hours == 2
    assert updated.resolution_time_hours == 12
    assert updated.escalation_role == "SUPER_ADMIN"


def test_edit_user_security_guards(db_session):
    """Test editing user details and role change validation guards."""
    user_repo = UserRepository(db_session)
    
    # Create two users (one super admin and one citizen)
    sa_user = user_repo.create_user(email="sa@example.com", full_name="Super Admin", hashed_password="pwd", role=UserRole.SUPER_ADMIN.value)
    citizen = user_repo.create_user(email="c@example.com", full_name="Citizen", hashed_password="pwd", role=UserRole.CITIZEN.value)
    db_session.commit()
    
    # 1. Edit citizen details successfully
    updated, err = user_repo.update_user(citizen.id, full_name="Citizen New Name", email="c.new@example.com", role=UserRole.OFFICER.value, is_active=True)
    assert err is None
    assert updated is not None
    assert updated.full_name == "Citizen New Name"
    assert updated.role == UserRole.OFFICER.value
    
    # 2. Prevent Super Admin from demoting themselves
    updated_sa, err_sa = user_repo.update_user(
        user_id=sa_user.id,
        full_name="Super Admin",
        email="sa@example.com",
        role=UserRole.CITIZEN.value,
        is_active=True,
        caller_id=sa_user.id
    )
    assert updated_sa is None
    assert "cannot demote yourself" in err_sa
    
    # 3. Prevent Super Admin from deactivating themselves
    updated_act, err_act = user_repo.update_user(
        user_id=sa_user.id,
        full_name="Super Admin",
        email="sa@example.com",
        role=UserRole.SUPER_ADMIN.value,
        is_active=False,
        caller_id=sa_user.id
    )
    assert updated_act is None
    assert "cannot deactivate your own account" in err_act
