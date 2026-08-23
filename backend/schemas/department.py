"""Pydantic schemas for Departments, Categories, and Wards."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class DepartmentCreateSchema(BaseModel):
    """Department creation schema."""

    name: str = Field(..., min_length=3, max_length=150)
    code: str = Field(..., min_length=2, max_length=20)
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class CategoryCreateSchema(BaseModel):
    """Complaint Category creation schema."""

    name: str = Field(..., min_length=2, max_length=150)
    slug: str = Field(..., min_length=2, max_length=150)
    department_id: str
    icon: str = "📌"
    description: Optional[str] = None
    default_severity: str = "MEDIUM"


class WardCreateSchema(BaseModel):
    """Ward creation schema."""

    name: str = Field(..., min_length=2, max_length=150)
    ward_number: Optional[int] = None
    zone: str = Field(..., min_length=2, max_length=100)
    city: str = "Mumbai"
    state: str = "Maharashtra"
    pincode: Optional[str] = None
    center_latitude: Optional[float] = None
    center_longitude: Optional[float] = None

    @field_validator("pincode")
    @classmethod
    def validate_indian_pincode(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "":
            v_clean = v.strip()
            if not v_clean.isdigit() or len(v_clean) != 6:
                raise ValueError("Pincode must be a valid Indian pincode containing exactly 6 digits.")
            return v_clean
        return v

