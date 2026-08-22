"""Configurable Complaint Routing Engine."""

from typing import Optional, Tuple
from sqlalchemy.orm import Session
from backend.repositories.routing_repo import RoutingRepository
from backend.repositories.category_repo import CategoryRepository
from backend.repositories.user_repo import UserRepository
from backend.models.department import Department
from backend.models.user import Officer
from backend.utils.logging import logger


class RoutingService:
    """Evaluates configurable database routing rules to route complaints to the appropriate department."""

    def __init__(self, session: Session):
        self.session = session
        self.routing_repo = RoutingRepository(session)
        self.category_repo = CategoryRepository(session)
        self.user_repo = UserRepository(session)

    def route_complaint(
        self,
        category_id: str,
        ward_id: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Tuple[str, str, Optional[str]]:
        """
        Determine target department and route reason.
        Returns: (department_id, route_reason, optional_assigned_officer_id)
        """
        # 1. Evaluate database routing rules
        matching_rule = self.routing_repo.find_matching_rule(
            category_id=category_id,
            ward_id=ward_id,
            city=city,
        )

        if matching_rule:
            dept_id = matching_rule.target_department_id
            reason = f"Routed via rule '{matching_rule.name}' (Priority {matching_rule.priority_order})"
            logger.info(f"Complaint routed by rule: {reason} -> Dept {dept_id}")
        else:
            # 2. Fallback to category's default department
            category = self.category_repo.get_by_id(category_id)
            if not category:
                raise ValueError(f"Invalid category ID: {category_id}")
            dept_id = category.department_id
            reason = f"Routed to default department for category '{category.name}'"
            logger.info(f"Complaint routed by category default: {reason} -> Dept {dept_id}")

        # 3. Find available officer in department (preferably matching ward)
        dept_officers = self.user_repo.list_officers_by_department(dept_id)
        assigned_officer_id = None

        if dept_officers:
            # Prefer officer mapped to this ward
            ward_officers = [o for o in dept_officers if o.ward_id == ward_id]
            if ward_officers:
                assigned_officer_id = ward_officers[0].id
            else:
                assigned_officer_id = dept_officers[0].id

        return dept_id, reason, assigned_officer_id
