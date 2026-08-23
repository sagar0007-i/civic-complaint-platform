"""Department and Ward Repositories."""

from typing import Optional, List
from sqlalchemy.orm import Session
from backend.models.department import Department
from backend.models.ward import Ward



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

    def get_by_code_exclude(self, code: str, exclude_id: Optional[str] = None) -> Optional[Department]:
        query = self.session.query(Department).filter(Department.code == code.strip().upper())
        if exclude_id:
            query = query.filter(Department.id != exclude_id)
        return query.first()

    def update(
        self,
        dept_id: str,
        name: str,
        code: str,
        description: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        is_active: bool = True,
    ) -> Optional[Department]:
        dept = self.get_by_id(dept_id)
        if not dept:
            return None
        dept.name = name.strip()
        dept.code = code.strip().upper()
        dept.description = description
        dept.contact_email = contact_email
        dept.contact_phone = contact_phone
        dept.is_active = is_active
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

    def update(
        self,
        ward_id: str,
        name: str,
        zone: str,
        ward_number: Optional[int] = None,
        city: str = "Mumbai",
        state: str = "Maharashtra",
        pincode: Optional[str] = None,
        center_lat: Optional[float] = None,
        center_lng: Optional[float] = None,
        is_active: bool = True,
    ) -> Optional[Ward]:
        ward = self.get_by_id(ward_id)
        if not ward:
            return None
        ward.name = name.strip()
        ward.zone = zone.strip()
        ward.ward_number = ward_number
        ward.city = city.strip()
        ward.state = state.strip()
        ward.pincode = pincode
        ward.center_latitude = center_lat
        ward.center_longitude = center_lng
        ward.is_active = is_active
        self.session.flush()
        return ward

    def get_by_number_and_zone(self, ward_number: int, zone: str, exclude_id: Optional[str] = None) -> Optional[Ward]:
        query = self.session.query(Ward).filter(Ward.ward_number == ward_number, Ward.zone == zone)
        if exclude_id:
            query = query.filter(Ward.id != exclude_id)
        return query.first()


