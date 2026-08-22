"""Government / Municipal ULB Integration Gateway Abstraction."""

from typing import Dict, Any, Optional
from backend.models.complaint import Complaint
from backend.utils.logging import logger


class MockGovernmentIntegrationService:
    """
    Mock gateway representing future real-time integrations with
    Municipal Corporation ERPs, Smart City Command Centers, or State Grievance Portals (e.g. CPGRAMS / IGRS).
    """

    def __init__(self, is_enabled: bool = True):
        self.is_enabled = is_enabled

    def forward_complaint_to_ulb(self, complaint: Complaint) -> Dict[str, Any]:
        """Simulate dispatch to municipal ERP webhook/API."""
        if not self.is_enabled:
            return {"status": "SKIPPED", "message": "Government integration is disabled in dev mode."}

        external_ref_id = f"ULB-GOV-{complaint.complaint_number}"
        logger.info(
            f"[MOCK GOV INTEGRATION] Dispatched complaint {complaint.complaint_number} to {complaint.department.name} (Ref: {external_ref_id})"
        )

        return {
            "status": "DISPATCHED",
            "external_reference_id": external_ref_id,
            "municipality": complaint.location.city if complaint.location else "Municipal Corporation",
            "department": complaint.department.name if complaint.department else "General Admin",
            "acknowledged": True,
        }
