"""Routing, SLA, Notification, and Audit Repositories."""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from backend.models.routing import RoutingRule
from backend.models.sla import SLARule, Escalation
from backend.models.notification import Notification, NotificationChannel
from backend.models.audit import AuditLog
from backend.models.complaint import Complaint, ComplaintStatus


class RoutingRepository:
    """Routing rules access."""

    def __init__(self, session: Session):
        self.session = session

    def get_all(self, active_only: bool = True) -> List[RoutingRule]:
        query = self.session.query(RoutingRule).options(
            joinedload(RoutingRule.category),
            joinedload(RoutingRule.ward),
            joinedload(RoutingRule.target_department),
        )
        if active_only:
            query = query.filter(RoutingRule.is_active == True)
        return query.order_by(RoutingRule.priority_order.asc()).all()

    def find_matching_rule(
        self,
        category_id: str,
        ward_id: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Optional[RoutingRule]:
        """
        Find highest priority active rule:
        1. Exact category + ward match
        2. Exact category + city match
        3. Exact category match
        """
        # 1. Ward match
        if ward_id:
            rule = (
                self.session.query(RoutingRule)
                .filter(
                    RoutingRule.category_id == category_id,
                    RoutingRule.ward_id == ward_id,
                    RoutingRule.is_active == True,
                )
                .order_by(RoutingRule.priority_order.asc())
                .first()
            )
            if rule:
                return rule

        # 2. City match
        if city:
            rule = (
                self.session.query(RoutingRule)
                .filter(
                    RoutingRule.category_id == category_id,
                    RoutingRule.city.ilike(city.strip()),
                    RoutingRule.is_active == True,
                )
                .order_by(RoutingRule.priority_order.asc())
                .first()
            )
            if rule:
                return rule

        # 3. Category fallback
        return (
            self.session.query(RoutingRule)
            .filter(
                RoutingRule.category_id == category_id,
                RoutingRule.ward_id.is_(None),
                RoutingRule.city.is_(None),
                RoutingRule.is_active == True,
            )
            .order_by(RoutingRule.priority_order.asc())
            .first()
        )

    def create(
        self,
        name: str,
        category_id: str,
        target_department_id: str,
        ward_id: Optional[str] = None,
        city: Optional[str] = None,
        priority_order: int = 10,
    ) -> RoutingRule:
        rule = RoutingRule(
            name=name.strip(),
            category_id=category_id,
            target_department_id=target_department_id,
            ward_id=ward_id,
            city=city.strip() if city else None,
            priority_order=priority_order,
            is_active=True,
        )
        self.session.add(rule)
        self.session.flush()
        return rule


class SLARepository:
    """SLA and Escalation rules access."""

    def __init__(self, session: Session):
        self.session = session

    def get_all(self, active_only: bool = True) -> List[SLARule]:
        query = self.session.query(SLARule).options(joinedload(SLARule.category))
        if active_only:
            query = query.filter(SLARule.is_active == True)
        return query.all()

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

    def get_overdue_complaints(self) -> List[Complaint]:
        """Fetch unresolved complaints past their SLA deadline."""
        now_utc = datetime.now(timezone.utc)
        now_naive = datetime.now()
        return (
            self.session.query(Complaint)
            .filter(
                Complaint.status.notin_([ComplaintStatus.RESOLVED.value, ComplaintStatus.REJECTED.value]),
                Complaint.sla_deadline.isnot(None),
                (Complaint.sla_deadline < now_utc) | (Complaint.sla_deadline < now_naive),
            )
            .all()
        )


class NotificationRepository:
    """Notifications access."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        user_id: str,
        title: str,
        message: str,
        complaint_id: Optional[str] = None,
        channel: str = NotificationChannel.IN_APP.value,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            complaint_id=complaint_id,
            title=title.strip(),
            message=message.strip(),
            channel=channel,
            is_read=False,
        )
        self.session.add(notif)
        self.session.flush()
        return notif

    def list_for_user(self, user_id: str, limit: int = 50) -> List[Notification]:
        return (
            self.session.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )

    def mark_as_read(self, notification_id: str) -> None:
        notif = self.session.query(Notification).filter(Notification.id == notification_id).first()
        if notif:
            notif.is_read = True
            self.session.flush()

    def mark_all_read(self, user_id: str) -> None:
        self.session.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).update(
            {"is_read": True}
        )
        self.session.flush()


class AuditRepository:
    """Audit Logging access."""

    def __init__(self, session: Session):
        self.session = session

    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details_json: Optional[str] = None,
    ) -> AuditLog:
        audit = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            user_id=user_id,
            ip_address=ip_address,
            details_json=details_json,
        )
        self.session.add(audit)
        self.session.flush()
        return audit

    def list_logs(self, limit: int = 100) -> List[AuditLog]:
        return (
            self.session.query(AuditLog)
            .options(joinedload(AuditLog.user))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
