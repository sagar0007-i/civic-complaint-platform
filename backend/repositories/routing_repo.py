"""Routing, Notification, and Audit Repositories."""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from backend.models.routing import RoutingRule
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

    def update(
        self,
        rule_id: str,
        name: str,
        category_id: str,
        target_department_id: str,
        ward_id: Optional[str] = None,
        city: Optional[str] = None,
        priority_order: int = 10,
        is_active: bool = True,
    ) -> Optional[RoutingRule]:
        rule = self.session.query(RoutingRule).filter(RoutingRule.id == rule_id).first()
        if not rule:
            return None
        rule.name = name.strip()
        rule.category_id = category_id
        rule.target_department_id = target_department_id
        rule.ward_id = ward_id
        rule.city = city.strip() if city else None
        rule.priority_order = priority_order
        rule.is_active = is_active
        self.session.flush()
        return rule




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
