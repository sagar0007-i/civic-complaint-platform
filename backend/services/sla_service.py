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

        has_justification = bool(getattr(complaint, "delay_reason", None))
        justification_text = getattr(complaint, "delay_reason", None)
        justified_by = getattr(complaint, "delay_justified_by", None)
        justified_at = getattr(complaint, "delay_justified_at", None)
        revised_target = getattr(complaint, "revised_resolution_target", None)

        if total_seconds < 0:
            overdue_hours = abs(total_seconds) / 3600

            # Auto-escalate if overdue by more than 24 hours and not yet escalated
            if overdue_hours >= 24.0 and not complaint.is_escalated:
                try:
                    self.sla_repo.log_escalation(
                        complaint_id=complaint.id,
                        reason=f"Auto-escalated: SLA breached and overdue by {overdue_hours:.1f}h (exceeding 24h threshold).",
                        escalated_to_role="DEPARTMENT_ADMIN",
                    )
                    complaint.is_escalated = True
                    try:
                        self.session.commit()
                    except Exception:
                        self.session.flush()
                    logger.warning(f"Complaint {complaint.complaint_number} auto-escalated on evaluation (overdue by {overdue_hours:.1f}h).")
                except Exception as e:
                    logger.error(f"Error during on-the-fly auto escalation of {complaint.complaint_number}: {e}")

            badge = f"🚨 Overdue by {overdue_hours:.1f}h"
            if getattr(complaint, "is_escalated", False):
                badge = f"🚨 Overdue by {overdue_hours:.1f}h [🔥 Escalated]"
            if has_justification:
                badge = f"🚨 Overdue ({overdue_hours:.1f}h) [📝 Reason Published]"

            return {
                "status": "BREACHED",
                "badge": badge,
                "is_breached": True,
                "is_escalated": getattr(complaint, "is_escalated", False),
                "overdue_hours": overdue_hours,
                "has_justification": has_justification,
                "delay_reason": justification_text,
                "delay_justified_by": justified_by,
                "delay_justified_at": justified_at,
                "revised_resolution_target": revised_target,
            }
        elif total_seconds < 3600 * 8:  # Less than 8 hours
            hours_left = total_seconds / 3600
            return {
                "status": "AT_RISK",
                "badge": f"⚠️ At Risk ({hours_left:.1f}h left)",
                "is_breached": False,
                "is_escalated": getattr(complaint, "is_escalated", False),
                "hours_left": hours_left,
                "has_justification": has_justification,
                "delay_reason": justification_text,
                "delay_justified_by": justified_by,
                "delay_justified_at": justified_at,
                "revised_resolution_target": revised_target,
            }
        else:
            hours_left = total_seconds / 3600
            return {
                "status": "ON_TRACK",
                "badge": f"🟢 On Track ({hours_left:.1f}h left)",
                "is_breached": False,
                "is_escalated": getattr(complaint, "is_escalated", False),
                "hours_left": hours_left,
                "has_justification": has_justification,
                "delay_reason": justification_text,
                "delay_justified_by": justified_by,
                "delay_justified_at": justified_at,
                "revised_resolution_target": revised_target,
            }

    def check_and_escalate_overdue_complaints(self, min_overdue_hours: float = 0.0) -> List[Escalation]:
        """Scan active complaints and escalate those past their deadline (optionally past min_overdue_hours)."""
        overdue_list = self.sla_repo.get_overdue_complaints(min_overdue_hours=min_overdue_hours)
        escalations_created = []
        now_utc = datetime.now(timezone.utc)

        for complaint in overdue_list:
            if not complaint.is_escalated:
                deadline = complaint.sla_deadline
                if deadline and deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                overdue_hours = (now_utc - deadline).total_seconds() / 3600.0 if deadline else 0.0

                threshold_str = f" (exceeded {min_overdue_hours:.0f}h threshold)" if min_overdue_hours > 0 else ""
                esc = self.sla_repo.log_escalation(
                    complaint_id=complaint.id,
                    reason=f"Auto-escalated: SLA breached. Complaint overdue by {overdue_hours:.1f}h{threshold_str} (deadline was {complaint.sla_deadline.strftime('%Y-%m-%d %H:%M UTC')}).",
                    escalated_to_role="DEPARTMENT_ADMIN",
                )
                escalations_created.append(esc)
                logger.warning(f"Complaint {complaint.complaint_number} auto-escalated due to SLA breach ({overdue_hours:.1f}h overdue).")

        if escalations_created:
            try:
                self.session.commit()
            except Exception:
                self.session.flush()

        return escalations_created
