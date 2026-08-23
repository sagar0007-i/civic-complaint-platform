"""User and Officer Repository."""

from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from backend.models.user import User, Officer, UserRole


class UserRepository:
    """Database operations for Users and Officers."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Fetch user by UUID with officer profile."""
        return (
            self.session.query(User)
            .options(joinedload(User.officer_profile).joinedload(Officer.department))
            .filter(User.id == user_id)
            .first()
        )

    def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by email (case-insensitive)."""
        return (
            self.session.query(User)
            .options(joinedload(User.officer_profile).joinedload(Officer.department))
            .filter(User.email.ilike(email.strip()))
            .first()
        )

    def create_user(
        self,
        email: str,
        full_name: str,
        hashed_password: str,
        phone: Optional[str] = None,
        role: str = UserRole.CITIZEN.value,
    ) -> User:
        """Create a new user."""
        user = User(
            email=email.strip().lower(),
            full_name=full_name.strip(),
            hashed_password=hashed_password,
            phone=phone.strip() if phone else None,
            role=role,
            is_active=True,
        )
        self.session.add(user)
        self.session.flush()
        return user

    def list_users(self, role: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[User]:
        """List users optionally filtered by role."""
        query = self.session.query(User).options(joinedload(User.officer_profile))
        if role:
            query = query.filter(User.role == role)
        return query.order_by(User.created_at.desc()).limit(limit).offset(offset).all()

    def update_role(self, user_id: str, new_role: str) -> Optional[User]:
        """Update user role."""
        user = self.get_by_id(user_id)
        if user:
            user.role = new_role
            self.session.flush()
        return user

    def update_password(self, user_id: str, new_hashed_password: str) -> Optional[User]:
        """Update hashed password for a user."""
        user = self.get_by_id(user_id)
        if user:
            user.hashed_password = new_hashed_password
            self.session.flush()
        return user

    def update_user(
        self,
        user_id: str,
        full_name: str,
        email: str,
        role: str,
        is_active: bool = True,
        caller_id: Optional[str] = None,
    ) -> tuple[Optional[User], Optional[str]]:
        """Update user account details with security guards."""
        user = self.get_by_id(user_id)
        if not user:
            return None, "User not found."

        # Self-demotion / deactivation protection
        if caller_id and user.id == caller_id:
            if user.role == UserRole.SUPER_ADMIN.value and role != UserRole.SUPER_ADMIN.value:
                return None, "You cannot demote yourself from Super Admin."
            if not is_active:
                return None, "You cannot deactivate your own account."

        # Check unique email constraint
        clean_email = email.strip().lower()
        if user.email.lower() != clean_email:
            existing = self.get_by_email(clean_email)
            if existing:
                return None, "A user with this email already exists."

        user.full_name = full_name.strip()
        user.email = clean_email
        user.role = role
        user.is_active = is_active
        self.session.flush()
        return user, None



    def create_officer_profile(
        self,
        user_id: str,
        department_id: str,
        employee_code: str,
        designation: str = "Junior Engineer",
        ward_id: Optional[str] = None,
    ) -> Officer:
        """Create an officer profile for a user."""
        officer = Officer(
            user_id=user_id,
            department_id=department_id,
            ward_id=ward_id,
            designation=designation,
            employee_code=employee_code,
            is_available=True,
        )
        self.session.add(officer)
        self.session.flush()
        return officer

    def get_officer_by_user_id(self, user_id: str) -> Optional[Officer]:
        """Fetch officer profile by user_id."""
        return (
            self.session.query(Officer)
            .options(joinedload(Officer.department), joinedload(Officer.ward), joinedload(Officer.user))
            .filter(Officer.user_id == user_id)
            .first()
        )

    def list_officers_by_department(self, department_id: str) -> List[Officer]:
        """Fetch all officers in a specific department."""
        return (
            self.session.query(Officer)
            .options(joinedload(Officer.user), joinedload(Officer.ward))
            .filter(Officer.department_id == department_id, Officer.is_available == True)
            .all()
        )

    def get_officer_by_employee_code(self, employee_code: str) -> Optional[Officer]:
        """Fetch officer profile by employee code."""
        if not employee_code:
            return None
        return (
            self.session.query(Officer)
            .filter(Officer.employee_code == employee_code.strip())
            .first()
        )

