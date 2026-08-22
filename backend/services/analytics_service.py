"""Civic Analytics and Reporting Service."""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.models.complaint import Complaint, ComplaintStatus, ComplaintSeverity
from backend.models.department import Department
from backend.models.category import ComplaintCategory
from backend.models.ward import Ward


class AnalyticsService:
    """Provides statistical aggregations and analytics metrics for dashboards."""

    def __init__(self, session: Session):
        self.session = session

    def get_summary_kpis(self, department_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch overall KPI metrics."""
        query = self.session.query(Complaint)
        if department_id:
            query = query.filter(Complaint.department_id == department_id)

        total = query.count()
        submitted = query.filter(Complaint.status == ComplaintStatus.SUBMITTED.value).count()
        in_progress = query.filter(
            Complaint.status.in_(
                [
                    ComplaintStatus.ACKNOWLEDGED.value,
                    ComplaintStatus.ASSIGNED.value,
                    ComplaintStatus.IN_PROGRESS.value,
                    ComplaintStatus.WAITING_FOR_INFORMATION.value,
                ]
            )
        ).count()
        resolved = query.filter(Complaint.status == ComplaintStatus.RESOLVED.value).count()
        rejected = query.filter(Complaint.status == ComplaintStatus.REJECTED.value).count()
        escalated = query.filter(Complaint.is_escalated == True).count()

        # Calculate average resolution time for resolved complaints
        resolved_complaints = (
            self.session.query(Complaint.created_at, Complaint.resolved_at)
            .filter(
                Complaint.status == ComplaintStatus.RESOLVED.value,
                Complaint.resolved_at.isnot(None),
            )
        )
        if department_id:
            resolved_complaints = resolved_complaints.filter(Complaint.department_id == department_id)

        resolved_list = resolved_complaints.all()
        avg_res_hours = 0.0
        if resolved_list:
            durations = [(r.resolved_at - r.created_at).total_seconds() / 3600 for r in resolved_list if r.resolved_at]
            if durations:
                avg_res_hours = round(sum(durations) / len(durations), 1)

        resolution_rate = round((resolved / total * 100) if total > 0 else 0.0, 1)

        return {
            "total": total,
            "submitted": submitted,
            "in_progress": in_progress,
            "resolved": resolved,
            "rejected": rejected,
            "escalated": escalated,
            "resolution_rate": resolution_rate,
            "avg_resolution_hours": avg_res_hours,
        }

    def get_category_breakdown(self, department_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Complaints count by category."""
        query = (
            self.session.query(
                ComplaintCategory.name,
                ComplaintCategory.icon,
                func.count(Complaint.id).label("count"),
            )
            .join(Complaint, Complaint.category_id == ComplaintCategory.id, isouter=True)
        )
        if department_id:
            query = query.filter(Complaint.department_id == department_id)

        rows = query.group_by(ComplaintCategory.name, ComplaintCategory.icon).order_by(func.count(Complaint.id).desc()).all()
        return [{"category": f"{r.icon} {r.name}", "count": r.count} for r in rows if r.count > 0]

    def get_department_breakdown(self) -> List[Dict[str, Any]]:
        """Complaints count by department."""
        rows = (
            self.session.query(
                Department.name,
                Department.code,
                func.count(Complaint.id).label("count"),
            )
            .join(Complaint, Complaint.department_id == Department.id, isouter=True)
            .group_by(Department.name, Department.code)
            .order_by(func.count(Complaint.id).desc())
            .all()
        )
        return [{"department": r.name, "code": r.code, "count": r.count} for r in rows if r.count > 0]

    def get_ward_breakdown(self) -> List[Dict[str, Any]]:
        """Complaints count by ward/zone."""
        rows = (
            self.session.query(
                Ward.name,
                Ward.zone,
                Ward.city,
                func.count(Complaint.id).label("count"),
            )
            .join(Complaint, Complaint.ward_id == Ward.id, isouter=True)
            .group_by(Ward.name, Ward.zone, Ward.city)
            .order_by(func.count(Complaint.id).desc())
            .all()
        )
        return [{"ward": f"{r.name} ({r.zone})", "city": r.city, "count": r.count} for r in rows if r.count > 0]

    def get_severity_breakdown(self) -> List[Dict[str, Any]]:
        """Complaints count by severity."""
        rows = (
            self.session.query(
                Complaint.severity,
                func.count(Complaint.id).label("count"),
            )
            .group_by(Complaint.severity)
            .all()
        )
        return [{"severity": r.severity, "count": r.count} for r in rows]

    def get_public_resolved_showcase(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Public list of recent resolved complaints for transparency & citizen trust."""
        complaints = (
            self.session.query(Complaint)
            .filter(Complaint.status == ComplaintStatus.RESOLVED.value)
            .order_by(Complaint.resolved_at.desc())
            .limit(limit)
            .all()
        )

        showcase = []
        for c in complaints:
            showcase.append(
                {
                    "complaint_number": c.complaint_number,
                    "title": c.title,
                    "category": c.category.name if c.category else "Civic Issue",
                    "category_icon": c.category.icon if c.category else "📌",
                    "department": c.department.name if c.department else "",
                    "ward": c.ward.name if c.ward else (c.location.city if c.location else "City"),
                    "created_at": c.created_at,
                    "resolved_at": c.resolved_at or c.updated_at,
                }
            )
        return showcase
