"""Complaint Routing Engine Tests."""

import pytest
from backend.services.routing_service import RoutingService
from backend.repositories.routing_repo import RoutingRepository


def test_routing_by_rule_priority(db_session, seed_test_data):
    """Test routing matches active database rules."""
    routing_service = RoutingService(db_session)
    data = seed_test_data

    # Garbage -> Sanitation (DEPT_SWM)
    dept_id, reason, officer_id = routing_service.route_complaint(
        category_id=data["cat_garbage"].id,
        ward_id=data["ward"].id,
        city="Mumbai",
    )
    assert dept_id == data["dept_swm"].id
    assert "Routed via rule" in reason


def test_routing_category_fallback(db_session, seed_test_data):
    """Test fallback to category's default department when no custom rule exists."""
    routing_service = RoutingService(db_session)
    routing_repo = RoutingRepository(db_session)
    data = seed_test_data

    # Delete routing rule for Pothole to test category fallback
    db_session.query(routing_repo.get_all()[0].__class__).filter_by(category_id=data["cat_pothole"].id).delete()
    db_session.flush()

    dept_id, reason, _ = routing_service.route_complaint(
        category_id=data["cat_pothole"].id,
        ward_id=data["ward"].id,
    )
    assert dept_id == data["dept_roads"].id
    assert "default department" in reason
