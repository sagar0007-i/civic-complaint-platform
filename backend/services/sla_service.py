"""SLA and Escalation Service."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.repositories.sla_repo import SLARepository
from backend.models.complaint import Complaint, ComplaintStatus
from backend.models.sla import SLARule, Escalation
from backend.utils.logging import logger


class SLAService:
    """Calculates SLA deadlines, evaluates breaches, and executes escalations."""

    def __init__(self, session: Session):
        self.session = session
        self.sla_repo = SLARepository(session)

    def calculate_deadline(self, category_id: Optional[str], severity: Optional[str]) -> tuple[datetime, int, int]:
        """
        Calculate SLA resolution deadline based on matching SLA rule.
        Returns: (sla_deadline, response_hours, resolution_hours)
        """
        rule = self.sla_repo.get_matching_rule(category_id=category_id, severity=severity)

        if rule:
            res_hours = rule.resolution_time_hours
            resp_hours = rule.response_time_hours
        else:
            # Default fallback SLAs by severity
            defaults = {
                "CRITICAL": (4, 12),
                "HIGH": (12, 24),
                "MEDIUM": (24, 72),
                "LOW": (48, 120),
            }
            resp_hours, res_hours = defaults.get(severity or "MEDIUM", (24, 72))

        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=res_hours)
        return deadline, resp_hours, res_hours

    def check_sla_status(self, complaint: Complaint) -> Dict[str, Any]:
        """Evaluate whether a complaint is on track, at risk, or breached."""
        if complaint.status in [ComplaintStatus.RESOLVED.value, ComplaintStatus.REJECTED.value]:
            return {"status": "RESOLVED", "badge": "✅ Completed", "is_breached": False}

        if not complaint.sla_deadline:
            return {"status": "NO_SLA", "badge": "⚪ Standard", "is_breached": False}

        now = datetime.now(timezone.utc)
        deadline = complaint.sla_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        time_left = deadline - now
        total_seconds = time_left.total_seconds()

        if total_seconds < 0:
            overdue_hours = abs(total_seconds) / 3600
            return {
                "status": "BREACHED",
                "badge": f"🚨 Overdue by {overdue_hours:.1f}h",
                "is_breached": True,
                "overdue_hours": overdue_hours,
            }
        elif total_seconds < 3600 * 8:  # Less than 8 hours
            hours_left = total_seconds / 3600
            return {
                "status": "AT_RISK",
                "badge": f"⚠️ At Risk ({hours_left:.1f}h left)",
                "is_breached": False,
                "hours_left": hours_left,
            }
        else:
            hours_left = total_seconds / 3600
            return {
                "status": "ON_TRACK",
                "badge": f"🟢 On Track ({hours_left:.1f}h left)",
                "is_breached": False,
                "hours_left": hours_left,
            }

    def check_and_escalate_overdue_complaints(self) -> List[Escalation]:
        """Scan active complaints and escalate those past their deadline."""
        overdue_list = self.sla_repo.get_overdue_complaints()
        escalations_created = []

        for complaint in overdue_list:
            if not complaint.is_escalated:
                esc = self.sla_repo.log_escalation(
                    complaint_id=complaint.id,
                    reason=f"SLA breached. Complaint not resolved by deadline {complaint.sla_deadline.strftime('%Y-%m-%d %H:%M UTC')}.",
                    escalated_to_role="DEPARTMENT_ADMIN",
                )
                escalations_created.append(esc)
                logger.warning(f"Complaint {complaint.complaint_number} auto-escalated due to SLA breach.")

        return escalations_created
