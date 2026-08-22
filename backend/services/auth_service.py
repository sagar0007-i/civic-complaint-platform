"""Authentication and RBAC Authorization Service."""

import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.repositories.user_repo import UserRepository
from backend.repositories.audit_repo import AuditRepository
from backend.models.user import User, UserRole, Officer
from backend.schemas.user import UserRegisterSchema, UserLoginSchema
from backend.utils.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    generate_secure_token,
    sanitize_text,
)
from backend.utils.logging import logger


class AuthService:
    """Authentication, registration, and RBAC service."""

    def __init__(self, session: Session):
        self.session = session
        self.user_repo = UserRepository(session)
        self.audit_repo = AuditRepository(session)

    def register_citizen(self, data: UserRegisterSchema, ip_address: Optional[str] = None) -> tuple[Optional[User], Optional[str]]:
        """Register a new citizen account."""
        # 1. Check if email already exists
        existing = self.user_repo.get_by_email(data.email)
        if existing:
            return None, "An account with this email address already exists."

        # 2. Validate password strength
        is_valid, msg = validate_password_strength(data.password)
        if not is_valid:
            return None, msg

        # 3. Hash password and save
        hashed = hash_password(data.password)
        user = self.user_repo.create_user(
            email=data.email,
            full_name=sanitize_text(data.full_name),
            hashed_password=hashed,
            phone=data.phone,
            role=UserRole.CITIZEN.value,
        )

        # 4. Audit log
        self.audit_repo.log(
            action="AUTH_REGISTER",
            entity_type="User",
            entity_id=user.id,
            user_id=user.id,
            ip_address=ip_address,
            details_json=json.dumps({"email": user.email, "role": user.role}),
        )

        logger.info(f"Citizen registered successfully: {user.email}")
        return user, None

    def login(self, data: UserLoginSchema, ip_address: Optional[str] = None) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Authenticate user credentials and create session payload."""
        user = self.user_repo.get_by_email(data.email)
        if not user or not user.is_active:
            return None, "Invalid email or password."

        if not verify_password(data.password, user.hashed_password):
            return None, "Invalid email or password."

        # Generate session token
        token = generate_secure_token()

        # Audit log login
        self.audit_repo.log(
            action="AUTH_LOGIN",
            entity_type="User",
            entity_id=user.id,
            user_id=user.id,
            ip_address=ip_address,
            details_json=json.dumps({"email": user.email, "role": user.role}),
        )

        officer_info = None
        if user.officer_profile:
            officer_info = {
                "officer_id": user.officer_profile.id,
                "department_id": user.officer_profile.department_id,
                "department_name": user.officer_profile.department.name if user.officer_profile.department else "",
                "ward_id": user.officer_profile.ward_id,
                "designation": user.officer_profile.designation,
                "employee_code": user.officer_profile.employee_code,
            }

        session_payload = {
            "token": token,
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "role": user.role,
            "officer_profile": officer_info,
        }

        logger.info(f"User logged in successfully: {user.email} (Role: {user.role})")
        return session_payload, None

    def create_officer_account(
        self,
        email: str,
        full_name: str,
        password: str,
        department_id: str,
        employee_code: str,
        designation: str = "Junior Engineer",
        ward_id: Optional[str] = None,
        role: str = UserRole.OFFICER.value,
        admin_user_id: Optional[str] = None,
    ) -> tuple[Optional[User], Optional[str]]:
        """Admin helper to create an officer user account with profile."""
        existing = self.user_repo.get_by_email(email)
        if existing:
            return None, "A user with this email already exists."

        is_valid, msg = validate_password_strength(password)
        if not is_valid:
            return None, msg

        hashed = hash_password(password)
        user = self.user_repo.create_user(
            email=email,
            full_name=full_name,
            hashed_password=hashed,
            role=role,
        )

        self.user_repo.create_officer_profile(
            user_id=user.id,
            department_id=department_id,
            employee_code=employee_code,
            designation=designation,
            ward_id=ward_id,
        )

        self.audit_repo.log(
            action="CREATE_OFFICER",
            entity_type="Officer",
            entity_id=user.id,
            user_id=admin_user_id,
            details_json=json.dumps({"email": email, "role": role, "dept": department_id}),
        )

        return user, None
