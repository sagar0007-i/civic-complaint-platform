"""Department, Ward, and Category Repositories."""

from typing import Optional, List
from sqlalchemy.orm import Session
from backend.models.department import Department
from backend.models.ward import Ward
from backend.models.category import ComplaintCategory


class DepartmentRepository:
    """Operations for Government Departments."""

    def __init__(self, session: Session):
        self.session = session

    def get_all(self, active_only: bool = True) -> List[Department]:
        query = self.session.query(Department)
        if active_only:
            query = query.filter(Department.is_active == True)
        return query.order_by(Department.name.asc()).all()

    def get_by_id(self, dept_id: str) -> Optional[Department]:
        return self.session.query(Department).filter(Department.id == dept_id).first()

    def get_by_code(self, code: str) -> Optional[Department]:
        return self.session.query(Department).filter(Department.code == code).first()

    def create(
        self,
        name: str,
        code: str,
        description: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
    ) -> Department:
        dept = Department(
            name=name.strip(),
            code=code.strip().upper(),
            description=description,
            contact_email=contact_email,
            contact_phone=contact_phone,
            is_active=True,
        )
        self.session.add(dept)
        self.session.flush()
        return dept


class WardRepository:
    """Operations for Municipal Wards and Zones."""

    def __init__(self, session: Session):
        self.session = session

    def get_all(self, active_only: bool = True) -> List[Ward]:
        query = self.session.query(Ward)
        if active_only:
            query = query.filter(Ward.is_active == True)
        return query.order_by(Ward.city.asc(), Ward.zone.asc(), Ward.name.asc()).all()

    def get_by_id(self, ward_id: str) -> Optional[Ward]:
        return self.session.query(Ward).filter(Ward.id == ward_id).first()

    def create(
        self,
        name: str,
        zone: str,
        ward_number: Optional[int] = None,
        city: str = "Mumbai",
        state: str = "Maharashtra",
        pincode: Optional[str] = None,
        center_lat: Optional[float] = None,
        center_lng: Optional[float] = None,
    ) -> Ward:
        ward = Ward(
            name=name.strip(),
            zone=zone.strip(),
            ward_number=ward_number,
            city=city.strip(),
            state=state.strip(),
            pincode=pincode,
            center_latitude=center_lat,
            center_longitude=center_lng,
            is_active=True,
        )
        self.session.add(ward)
        self.session.flush()
        return ward


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
        return self.session.query(ComplaintCategory).filter(ComplaintCategory.slug == slug).first()

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
