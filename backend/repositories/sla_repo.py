"""SLA Repository Operations."""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from backend.models.sla import SLARule, Escalation
from backend.models.complaint import Complaint, ComplaintStatus


class SLARepository:
    """SLA and Escalation rules access."""

    def __init__(self, session: Session):
        self.session = session

    def get_all(self, active_only: bool = True) -> List[SLARule]:
        query = self.session.query(SLARule).options(joinedload(SLARule.category))
        if active_only:
            query = query.filter(SLARule.is_active == True)
        return query.all()

    def get_by_id(self, sla_id: str) -> Optional[SLARule]:
        return self.session.query(SLARule).filter(SLARule.id == sla_id).first()

    def get_matching_rule(self, category_id: Optional[str], severity: Optional[str]) -> Optional[SLARule]:
        """Find best matching SLA rule by category and severity."""
        # 1. Exact Category + Severity
        if category_id and severity:
            rule = (
                self.session.query(SLARule)
                .filter(
                    SLARule.category_id == category_id,
                    SLARule.severity == severity,
                    SLARule.is_active == True,
                )
                .first()
            )
            if rule:
                return rule

        # 2. Severity-only match
        if severity:
            rule = (
                self.session.query(SLARule)
                .filter(
                    SLARule.category_id.is_(None),
                    SLARule.severity == severity,
                    SLARule.is_active == True,
                )
                .first()
            )
            if rule:
                return rule

        # 3. Category-only match
        if category_id:
            rule = (
                self.session.query(SLARule)
                .filter(
                    SLARule.category_id == category_id,
                    SLARule.severity.is_(None),
                    SLARule.is_active == True,
                )
                .first()
            )
            if rule:
                return rule

        # 4. Default global fallback rule
        return self.session.query(SLARule).filter(SLARule.category_id.is_(None), SLARule.severity.is_(None), SLARule.is_active == True).first()

    def create(
        self,
        name: str,
        category_id: Optional[str] = None,
        severity: Optional[str] = None,
        response_time_hours: int = 24,
        resolution_time_hours: int = 72,
        escalation_role: str = "DEPARTMENT_ADMIN",
    ) -> SLARule:
        rule = SLARule(
            name=name.strip(),
            category_id=category_id,
            severity=severity,
            response_time_hours=response_time_hours,
            resolution_time_hours=resolution_time_hours,
            escalation_role=escalation_role,
            is_active=True,
        )
        self.session.add(rule)
        self.session.flush()
        return rule

    def update(
        self,
        sla_id: str,
        name: str,
        category_id: Optional[str] = None,
        severity: Optional[str] = None,
        response_time_hours: int = 24,
        resolution_time_hours: int = 72,
        escalation_role: str = "DEPARTMENT_ADMIN",
        is_active: bool = True,
    ) -> Optional[SLARule]:
        rule = self.get_by_id(sla_id)
        if not rule:
            return None
        rule.name = name.strip()
        rule.category_id = category_id
        rule.severity = severity
        rule.response_time_hours = response_time_hours
        rule.resolution_time_hours = resolution_time_hours
        rule.escalation_role = escalation_role
        rule.is_active = is_active
        self.session.flush()
        return rule

    def log_escalation(self, complaint_id: str, reason: str, escalated_to_role: str = "DEPARTMENT_ADMIN") -> Escalation:
        esc = Escalation(
            complaint_id=complaint_id,
            reason=reason,
            escalated_to_role=escalated_to_role,
            is_resolved=False,
        )
        self.session.add(esc)
        complaint = self.session.query(Complaint).filter(Complaint.id == complaint_id).first()
        if complaint:
            complaint.is_escalated = True
        self.session.flush()
        return esc

    def get_overdue_complaints(self, min_overdue_hours: float = 0.0) -> List[Complaint]:
        """Fetch unresolved complaints past their SLA deadline (optionally past min_overdue_hours)."""
        from datetime import timedelta
        now_utc = datetime.now(timezone.utc)
        now_naive = datetime.now()
        thresh_utc = now_utc - timedelta(hours=min_overdue_hours)
        thresh_naive = now_naive - timedelta(hours=min_overdue_hours)
        return (
            self.session.query(Complaint)
            .filter(
                Complaint.status.notin_([ComplaintStatus.RESOLVED.value, ComplaintStatus.REJECTED.value]),
                Complaint.sla_deadline.isnot(None),
                (Complaint.sla_deadline <= thresh_utc) | (Complaint.sla_deadline <= thresh_naive),
            )
            .all()
        )
