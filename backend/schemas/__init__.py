"""All Pydantic validation schemas."""

from backend.schemas.user import (
    UserRegisterSchema,
    UserLoginSchema,
    UserResponseSchema,
    OfficerCreateSchema,
    OfficerResponseSchema,
)
from backend.schemas.complaint import (
    LocationCreateSchema,
    MediaUploadMetaSchema,
    ComplaintCreateSchema,
    ComplaintStatusUpdateSchema,
    ComplaintAssignSchema,
    ComplaintCommentCreateSchema,
    ComplaintResponseSchema,
)
from backend.schemas.department import (
    DepartmentCreateSchema,
    CategoryCreateSchema,
    WardCreateSchema,
)
from backend.schemas.routing import RoutingRuleCreateSchema, SLARuleCreateSchema

__all__ = [
    "UserRegisterSchema",
    "UserLoginSchema",
    "UserResponseSchema",
    "OfficerCreateSchema",
    "OfficerResponseSchema",
    "LocationCreateSchema",
    "MediaUploadMetaSchema",
    "ComplaintCreateSchema",
    "ComplaintStatusUpdateSchema",
    "ComplaintAssignSchema",
    "ComplaintCommentCreateSchema",
    "ComplaintResponseSchema",
    "DepartmentCreateSchema",
    "CategoryCreateSchema",
    "WardCreateSchema",
    "RoutingRuleCreateSchema",
    "SLARuleCreateSchema",
]
