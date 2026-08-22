"""Pydantic validation schemas for Complaints, Media, Location, and Timeline."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from backend.models.complaint import ComplaintStatus, ComplaintSeverity


class LocationCreateSchema(BaseModel):
    """Complaint location creation."""

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    address: Optional[str] = None
    landmark: Optional[str] = None
    accuracy_meters: Optional[float] = None
    city: str = "Mumbai"
    ward_name: Optional[str] = None
    pincode: Optional[str] = None


class MediaUploadMetaSchema(BaseModel):
    """Metadata of an uploaded media file."""

    file_name: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    storage_provider: str = "local"
    storage_path: str
    file_hash: Optional[str] = None
    media_type: str = "image"  # image or video
    is_public: bool = True


class ComplaintCreateSchema(BaseModel):
    """Citizen complaint submission request."""

    category_id: str
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    severity: ComplaintSeverity = ComplaintSeverity.MEDIUM
    landmark: Optional[str] = Field(None, max_length=200)
    ward_id: Optional[str] = None

    # Embedded location
    location: LocationCreateSchema

    # Attached media list
    media_files: List[MediaUploadMetaSchema] = []


class ComplaintStatusUpdateSchema(BaseModel):
    """Officer / Admin status update payload."""

    to_status: ComplaintStatus
    remarks: Optional[str] = Field(None, max_length=2000)
    is_internal_note: bool = False


class ComplaintAssignSchema(BaseModel):
    """Complaint assignment payload."""

    officer_id: str
    department_id: Optional[str] = None
    note: Optional[str] = None


class ComplaintCommentCreateSchema(BaseModel):
    """Comment addition payload."""

    comment: str = Field(..., min_length=2, max_length=2000)
    is_internal: bool = False


class ComplaintResponseSchema(BaseModel):
    """Full Complaint representation."""

    model_config = {"from_attributes": True}

    id: str
    complaint_number: str
    citizen_id: str
    category_id: str
    department_id: str
    assigned_officer_id: Optional[str] = None
    ward_id: Optional[str] = None
    title: str
    description: str
    severity: str
    status: str
    landmark: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    is_escalated: bool
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
