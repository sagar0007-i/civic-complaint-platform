"""Pydantic schemas for Routing Rules and SLA Rules."""

from typing import Optional
from pydantic import BaseModel, Field


class RoutingRuleCreateSchema(BaseModel):
    """Routing rule payload."""

    name: str = Field(..., min_length=3, max_length=150)
    category_id: str
    ward_id: Optional[str] = None
    city: Optional[str] = None
    target_department_id: str
    priority_order: int = 10
    is_active: bool = True


class SLARuleCreateSchema(BaseModel):
    """SLA Rule payload."""

    name: str = Field(..., min_length=3, max_length=150)
    category_id: Optional[str] = None
    severity: Optional[str] = None  # LOW, MEDIUM, HIGH, CRITICAL, or None
    response_time_hours: int = Field(default=24, ge=1, le=720)
    resolution_time_hours: int = Field(default=72, ge=1, le=1440)
    escalation_role: str = "DEPARTMENT_ADMIN"
    is_active: bool = True
