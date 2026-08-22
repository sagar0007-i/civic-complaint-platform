"""Pydantic validation schemas for Users, Auth, and Officers."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from backend.models.user import UserRole


class UserRegisterSchema(BaseModel):
    """Citizen / User self-registration schema."""

    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    phone: Optional[str] = Field(None, pattern=r"^[0-9+\-\s()]{7,20}$")
    password: str = Field(..., min_length=8)


class UserLoginSchema(BaseModel):
    """User login request schema."""

    email: EmailStr
    password: str


class UserResponseSchema(BaseModel):
    """User profile response."""

    model_config = {"from_attributes": True}

    id: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool


class OfficerCreateSchema(BaseModel):
    """Officer profile creation."""

    user_id: str
    department_id: str
    ward_id: Optional[str] = None
    designation: str = "Junior Engineer"
    employee_code: str


class OfficerResponseSchema(BaseModel):
    """Officer profile response."""

    model_config = {"from_attributes": True}

    id: str
    user_id: str
    department_id: str
    ward_id: Optional[str] = None
    designation: str
    employee_code: str
    is_available: bool
    user: Optional[UserResponseSchema] = None
