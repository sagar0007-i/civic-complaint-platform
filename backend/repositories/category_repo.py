"""Category Repository Operations."""

from typing import Optional, List
from sqlalchemy.orm import Session
from backend.models.category import ComplaintCategory


class CategoryRepository:
    """Operations for Complaint Categories."""

    def __init__(self, session: Session):
        self.session = session

    def get_all(self, active_only: bool = True) -> List[ComplaintCategory]:
        query = self.session.query(ComplaintCategory)
        if active_only:
            query = query.filter(ComplaintCategory.is_active == True)
        return query.order_by(ComplaintCategory.name.asc()).all()

    def get_by_id(self, cat_id: str) -> Optional[ComplaintCategory]:
        return self.session.query(ComplaintCategory).filter(ComplaintCategory.id == cat_id).first()

    def get_by_slug(self, slug: str) -> Optional[ComplaintCategory]:
        return self.session.query(ComplaintCategory).filter(ComplaintCategory.slug == slug.strip().lower()).first()

    def get_by_slug_exclude(self, slug: str, exclude_id: Optional[str] = None) -> Optional[ComplaintCategory]:
        query = self.session.query(ComplaintCategory).filter(ComplaintCategory.slug == slug.strip().lower())
        if exclude_id:
            query = query.filter(ComplaintCategory.id != exclude_id)
        return query.first()

    def create(
        self,
        name: str,
        slug: str,
        department_id: str,
        icon: str = "📌",
        description: Optional[str] = None,
        default_severity: str = "MEDIUM",
    ) -> ComplaintCategory:
        cat = ComplaintCategory(
            name=name.strip(),
            slug=slug.strip().lower(),
            department_id=department_id,
            icon=icon,
            description=description,
            default_severity=default_severity,
            is_active=True,
        )
        self.session.add(cat)
        self.session.flush()
        return cat

    def update(
        self,
        cat_id: str,
        name: str,
        slug: str,
        department_id: str,
        icon: str = "📌",
        description: Optional[str] = None,
        default_severity: str = "MEDIUM",
        is_active: bool = True,
    ) -> Optional[ComplaintCategory]:
        cat = self.get_by_id(cat_id)
        if not cat:
            return None
        cat.name = name.strip()
        cat.slug = slug.strip().lower()
        cat.department_id = department_id
        cat.icon = icon
        cat.description = description
        cat.default_severity = default_severity
        cat.is_active = is_active
        self.session.flush()
        return cat
