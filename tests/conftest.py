"""Pytest configuration and database fixtures."""

import os
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.database import Base
from backend.models.user import User, Officer, UserRole
from backend.models.department import Department
from backend.models.ward import Ward
from backend.models.category import ComplaintCategory
from backend.models.routing import RoutingRule
from backend.models.sla import SLARule
from backend.utils.security import hash_password


@pytest.fixture(scope="session")
def engine():
    """Create in-memory SQLite database for fast isolated unit testing."""
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    return test_engine


@pytest.fixture(scope="function")
def db_session(engine):
    """Provide a transactional database session rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def seed_test_data(db_session):
    """Seed minimal core entities for test execution."""
    # 1. Ward
    ward = Ward(
        name="Ward H/West (Bandra West)",
        ward_number=18,
        zone="Western Suburbs",
        city="Mumbai",
        state="Maharashtra",
        center_latitude=19.0596,
        center_longitude=72.8295,
    )
    db_session.add(ward)
    db_session.flush()

    # 2. Departments
    dept_swm = Department(name="Solid Waste Management", code="DEPT_SWM", is_active=True)
    dept_roads = Department(name="Roads & Infrastructure", code="DEPT_ROADS", is_active=True)
    db_session.add_all([dept_swm, dept_roads])
    db_session.flush()

    # 3. Categories
    cat_garbage = ComplaintCategory(
        name="Garbage Dump",
        slug="garbage",
        department_id=dept_swm.id,
        icon="🗑️",
        default_severity="MEDIUM",
    )
    cat_pothole = ComplaintCategory(
        name="Pothole",
        slug="pothole",
        department_id=dept_roads.id,
        icon="🚧",
        default_severity="HIGH",
    )
    db_session.add_all([cat_garbage, cat_pothole])
    db_session.flush()

    # 4. Routing Rules
    r1 = RoutingRule(name="Route Garbage", category_id=cat_garbage.id, target_department_id=dept_swm.id, priority_order=10)
    r2 = RoutingRule(name="Route Potholes", category_id=cat_pothole.id, target_department_id=dept_roads.id, priority_order=10)
    db_session.add_all([r1, r2])

    # 5. SLA Rules
    s1 = SLARule(name="High SLA", severity="HIGH", response_time_hours=6, resolution_time_hours=24)
    s2 = SLARule(name="Medium SLA", severity="MEDIUM", response_time_hours=12, resolution_time_hours=72)
    db_session.add_all([s1, s2])

    # 6. Users
    pwd_hash = hash_password("TestPassword@123")
    citizen = User(email="citizen.test@example.com", full_name="Test Citizen", hashed_password=pwd_hash, role=UserRole.CITIZEN.value)
    officer_u = User(email="officer.test@civicpulse.gov.in", full_name="Test Officer", hashed_password=pwd_hash, role=UserRole.OFFICER.value)
    db_session.add_all([citizen, officer_u])
    db_session.flush()

    officer = Officer(user_id=officer_u.id, department_id=dept_swm.id, ward_id=ward.id, employee_code="OFF-TEST-01")
    db_session.add(officer)
    db_session.commit()

    return {
        "ward": ward,
        "dept_swm": dept_swm,
        "dept_roads": dept_roads,
        "cat_garbage": cat_garbage,
        "cat_pothole": cat_pothole,
        "citizen": citizen,
        "officer": officer,
    }
