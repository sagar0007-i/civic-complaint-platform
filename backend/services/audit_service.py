"""Audit Trail Logging Service."""

import json
from typing import Optional, Any, List
from sqlalchemy.orm import Session
from backend.repositories.audit_repo import AuditRepository
from backend.models.audit import AuditLog
from backend.utils.logging import logger


class AuditService:
    """Provides centralized audit logging for compliance and tracking."""

    def __init__(self, session: Session):
        self.session = session
        self.audit_repo = AuditRepository(session)

    def log_event(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        details_json = json.dumps(details, default=str) if details else None
        log = self.audit_repo.log(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            ip_address=ip_address,
            details_json=details_json,
        )
        logger.info(f"Audit log recorded: [{action}] {entity_type}:{entity_id} by User:{user_id}")
        return log

    def get_recent_logs(self, limit: int = 100) -> List[AuditLog]:
        """Fetch recent audit events for admin review."""
        return self.audit_repo.list_logs(limit=limit)
