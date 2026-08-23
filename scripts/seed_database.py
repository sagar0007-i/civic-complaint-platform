"""Database Seeder with realistic Mumbai, Maharashtra Municipal Civic Data (BMC / MCGM)."""

import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.database import init_db, get_db_session, engine, Base
from backend.models.user import User, Officer, UserRole
from backend.models.department import Department
from backend.models.ward import Ward
from backend.models.category import ComplaintCategory
from backend.models.routing import RoutingRule
from backend.models.sla import SLARule
from backend.models.complaint import Complaint, ComplaintStatus, ComplaintSeverity
from backend.models.location import ComplaintLocation
from backend.models.history import ComplaintStatusHistory
from backend.models.ai import AIClassification
from backend.models.notification import Notification, NotificationChannel
from backend.models.media import ComplaintMedia
from backend.utils.security import hash_password
from backend.utils.formatting import generate_complaint_id
from backend.utils.logging import logger


def seed_database(force_reseed: bool = True) -> None:
    """Populate database with complete production-like Mumbai, Maharashtra civic seed data."""
    logger.info("Initializing database tables...")
    
    if force_reseed:
        logger.info("Re-creating clean tables for Mumbai, Maharashtra...")
        Base.metadata.drop_all(bind=engine)
    
    init_db()

    with get_db_session() as session:
        # Check if already seeded
        existing_admin = session.query(User).filter(User.email == "admin@civicpulse.gov.in").first()
        if existing_admin:
            logger.info("Database already seeded. Skipping seed execution.")
            return

        logger.info("Seeding Mumbai Municipal Wards and Zones (BMC / MCGM)...")
        wards_data = [
            {"name": "Ward A (Colaba, Fort, Marine Drive)", "ward_number": 1, "zone": "South Mumbai Zone", "pincode": "400001", "lat": 18.9220, "lng": 72.8347},
            {"name": "Ward D (Malabar Hill, Walkeshwar, Girgaon)", "ward_number": 7, "zone": "South Mumbai Zone", "pincode": "400006", "lat": 18.9554, "lng": 72.8052},
            {"name": "Ward G/South (Worli, Lower Parel, Mahalaxmi)", "ward_number": 14, "zone": "City Zone", "pincode": "400018", "lat": 19.0020, "lng": 72.8250},
            {"name": "Ward H/West (Bandra West, Khar, Santacruz)", "ward_number": 18, "zone": "Western Suburbs", "pincode": "400050", "lat": 19.0596, "lng": 72.8295},
            {"name": "Ward K/West (Andheri West, Juhu, Versova)", "ward_number": 22, "zone": "Western Suburbs", "pincode": "400058", "lat": 19.1136, "lng": 72.8295},
            {"name": "Ward K/East (Andheri East, MIDC, Chakala)", "ward_number": 23, "zone": "Western Suburbs", "pincode": "400069", "lat": 19.1197, "lng": 72.8664},
            {"name": "Ward L (Kurla, Sakinaka, Chandivali)", "ward_number": 25, "zone": "Eastern Suburbs", "pincode": "400070", "lat": 19.0726, "lng": 72.8845},
            {"name": "Ward P/North (Malad West, Marve Road)", "ward_number": 31, "zone": "Western Suburbs", "pincode": "400064", "lat": 19.1860, "lng": 72.8485},
            {"name": "Ward R/Central (Borivali, Gorai, Eksar)", "ward_number": 35, "zone": "Western Suburbs", "pincode": "400092", "lat": 19.2307, "lng": 72.8567},
        ]
        ward_objs = {}
        for w in wards_data:
            ward = Ward(
                name=w["name"],
                ward_number=w["ward_number"],
                zone=w["zone"],
                city="Mumbai",
                state="Maharashtra",
                pincode=w["pincode"],
                center_latitude=w["lat"],
                center_longitude=w["lng"],
                is_active=True,
            )
            session.add(ward)
            session.flush()
            ward_objs[w["name"]] = ward

        logger.info("Seeding Mumbai Civic Departments (BMC / MCGM)...")
        depts_data = [
            {"name": "Solid Waste Management (SWM) - BMC", "code": "DEPT_SWM", "desc": "Garbage disposal, waste processing, street sweeping, and litter control", "email": "swm@civicpulse.gov.in"},
            {"name": "Hydraulic Engineer Department (BMC Water Works)", "code": "DEPT_BWSSB", "desc": "Potable water supply pipelines, underground water mains, and leak repairs", "email": "waterworks@civicpulse.gov.in"},
            {"name": "Mumbai Roads & Traffic Infrastructure (MCGM)", "code": "DEPT_ROADS", "desc": "Asphalt repairs, pothole filling, and arterial road resurfacing", "email": "roads@civicpulse.gov.in"},
            {"name": "BEST & Street Lighting Department", "code": "DEPT_ELEC", "desc": "LED streetlights, electrical poles, and public illumination", "email": "lighting@civicpulse.gov.in"},
            {"name": "Storm Water Drains Department (SWD - BMC)", "code": "DEPT_SWD", "desc": "Nullah cleaning, stormwater drain maintenance, and monsoon flood control", "email": "swd@civicpulse.gov.in"},
            {"name": "Public Health & Vector Control (BMC Health)", "code": "DEPT_HEALTH", "desc": "Public restrooms, vector fogging, malaria/dengue control, and hygiene inspections", "email": "health@civicpulse.gov.in"},
            {"name": "Public Works & General Infrastructure (BMC PWD)", "code": "DEPT_PWD", "desc": "Footpaths, promenades, flyover railings, public structures, and gardens", "email": "pwd@civicpulse.gov.in"},
        ]
        dept_objs = {}
        for d in depts_data:
            dept = Department(
                name=d["name"],
                code=d["code"],
                description=d["desc"],
                contact_email=d["email"],
                is_active=True,
            )
            session.add(dept)
            session.flush()
            dept_objs[d["code"]] = dept

        logger.info("Seeding Complaint Categories...")
        categories_data = [
            {"name": "Garbage Dump & Waste Accumulation", "slug": "garbage", "dept": "DEPT_SWM", "icon": "🗑️", "sev": "MEDIUM"},
            {"name": "Open Sewage & Manhole Overflow", "slug": "open-sewage", "dept": "DEPT_BWSSB", "icon": "🚰", "sev": "HIGH"},
            {"name": "Blocked Storm Drain & Clogged Nullah", "slug": "drainage", "dept": "DEPT_SWD", "icon": "🌊", "sev": "MEDIUM"},
            {"name": "Water Pipeline Leakage & Burst", "slug": "water-leakage", "dept": "DEPT_BWSSB", "icon": "💧", "sev": "HIGH"},
            {"name": "Water Supply Outage / Contamination", "slug": "water-supply", "dept": "DEPT_BWSSB", "icon": "🚱", "sev": "HIGH"},
            {"name": "Pothole & Damaged Road Surface", "slug": "pothole", "dept": "DEPT_ROADS", "icon": "🚧", "sev": "MEDIUM"},
            {"name": "Streetlight Not Working / Dark Stretch", "slug": "streetlight", "dept": "DEPT_ELEC", "icon": "💡", "sev": "LOW"},
            {"name": "Severe Flooding & Road Inundation", "slug": "flooding", "dept": "DEPT_SWD", "icon": "⛈️", "sev": "CRITICAL"},
            {"name": "Public Sanitation & Restroom Hygiene", "slug": "public-sanitation", "dept": "DEPT_HEALTH", "icon": "🚻", "sev": "MEDIUM"},
            {"name": "Illegal Debris & Construction Dumping", "slug": "illegal-dumping", "dept": "DEPT_SWM", "icon": "🚜", "sev": "MEDIUM"},
            {"name": "Damaged Footpath / Public Structure", "slug": "damaged-infrastructure", "dept": "DEPT_PWD", "icon": "🧱", "sev": "LOW"},
            {"name": "Other Civic Grievance", "slug": "other", "dept": "DEPT_PWD", "icon": "📌", "sev": "MEDIUM"},
        ]
        cat_objs = {}
        for c in categories_data:
            cat = ComplaintCategory(
                name=c["name"],
                slug=c["slug"],
                department_id=dept_objs[c["dept"]].id,
                icon=c["icon"],
                description=f"Citizen reporting category for {c['name'].lower()}",
                default_severity=c["sev"],
                is_active=True,
            )
            session.add(cat)
            session.flush()
            cat_objs[c["slug"]] = cat

        logger.info("Seeding Configurable Routing Rules...")
        for cat_slug, cat in cat_objs.items():
            rule = RoutingRule(
                name=f"Auto-Route {cat.name} to {cat.department.name}",
                category_id=cat.id,
                target_department_id=cat.department_id,
                priority_order=10,
                is_active=True,
            )
            session.add(rule)

        logger.info("Seeding SLA Rules...")
        sla_presets = [
            {"name": "Critical Emergency SLA (Flooding/Cave-in)", "sev": "CRITICAL", "resp": 2, "res": 8, "role": "SUPER_ADMIN"},
            {"name": "High Severity SLA (Water Burst/Sewage)", "sev": "HIGH", "resp": 6, "res": 24, "role": "DEPARTMENT_ADMIN"},
            {"name": "Medium Priority SLA (Potholes/Garbage)", "sev": "MEDIUM", "resp": 12, "res": 72, "role": "DEPARTMENT_ADMIN"},
            {"name": "Low Priority SLA (Streetlights/Footpath)", "sev": "LOW", "resp": 24, "res": 120, "role": "DEPARTMENT_ADMIN"},
        ]
        for s in sla_presets:
            sla = SLARule(
                name=s["name"],
                severity=s["sev"],
                response_time_hours=s["resp"],
                resolution_time_hours=s["res"],
                escalation_role=s["role"],
                is_active=True,
            )
            session.add(sla)

        logger.info("Seeding Users and Officers...")
        # Common passwords for easy local testing
        admin_pass = hash_password("Admin@123")
        officer_pass = hash_password("Officer@123")
        citizen_pass = hash_password("Citizen@123")

        # 1. Super Admin (BMC Municipal Commissioner)
        admin = User(
            email="admin@civicpulse.gov.in",
            full_name="Bhushan Gagrani (Municipal Commissioner, BMC)",
            phone="+91 98200 11001",
            hashed_password=admin_pass,
            role=UserRole.SUPER_ADMIN.value,
            is_active=True,
        )
        session.add(admin)

        # 2. Department Admin (Sanitation)
        dept_admin = User(
            email="admin.sanitation@civicpulse.gov.in",
            full_name="Dr. Sanjay Deshmukh (Chief Engineer, BMC SWM)",
            phone="+91 98200 11002",
            hashed_password=admin_pass,
            role=UserRole.DEPARTMENT_ADMIN.value,
            is_active=True,
        )
        session.add(dept_admin)

        # 3. Field Officer 1 (Sanitation - Bandra West Ward H/West)
        off_user1 = User(
            email="officer.sanitation@civicpulse.gov.in",
            full_name="Sachin Kadam",
            phone="+91 98200 22001",
            hashed_password=officer_pass,
            role=UserRole.OFFICER.value,
            is_active=True,
        )
        session.add(off_user1)
        session.flush()

        off1 = Officer(
            user_id=off_user1.id,
            department_id=dept_objs["DEPT_SWM"].id,
            ward_id=ward_objs["Ward H/West (Bandra West, Khar, Santacruz)"].id,
            designation="Senior Sanitary Inspector (Ward H/West)",
            employee_code="BMC-SWM-HW-042",
            is_available=True,
        )
        session.add(off1)

        # 4. Field Officer 2 (Roads - Andheri West Ward K/West)
        off_user2 = User(
            email="officer.roads@civicpulse.gov.in",
            full_name="Pradeep Sawant",
            phone="+91 98200 22002",
            hashed_password=officer_pass,
            role=UserRole.OFFICER.value,
            is_active=True,
        )
        session.add(off_user2)
        session.flush()

        off2 = Officer(
            user_id=off_user2.id,
            department_id=dept_objs["DEPT_ROADS"].id,
            ward_id=ward_objs["Ward K/West (Andheri West, Juhu, Versova)"].id,
            designation="Assistant Engineer (Roads & Traffic, Ward K/West)",
            employee_code="BMC-RDS-KW-088",
            is_available=True,
        )
        session.add(off2)

        # 5. Field Officer 3 (Water Works - Colaba Ward A)
        off_user3 = User(
            email="officer.water@civicpulse.gov.in",
            full_name="Pooja Shinde",
            phone="+91 98200 22003",
            hashed_password=officer_pass,
            role=UserRole.OFFICER.value,
            is_active=True,
        )
        session.add(off_user3)
        session.flush()

        off3 = Officer(
            user_id=off_user3.id,
            department_id=dept_objs["DEPT_BWSSB"].id,
            ward_id=ward_objs["Ward A (Colaba, Fort, Marine Drive)"].id,
            designation="Sub-Engineer (Hydraulic Dept, Ward A)",
            employee_code="BMC-WTR-A-105",
            is_available=True,
        )
        session.add(off3)

        # 6. Field Officer 4 (Storm Water Drains - Kurla Ward L)
        off_user4 = User(
            email="officer.swd@civicpulse.gov.in",
            full_name="Kishore More",
            phone="+91 98200 22004",
            hashed_password=officer_pass,
            role=UserRole.OFFICER.value,
            is_active=True,
        )
        session.add(off_user4)
        session.flush()

        off4 = Officer(
            user_id=off_user4.id,
            department_id=dept_objs["DEPT_SWD"].id,
            ward_id=ward_objs["Ward L (Kurla, Sakinaka, Chandivali)"].id,
            designation="Junior Engineer (SWD Monsoon Cell, Ward L)",
            employee_code="BMC-SWD-L-055",
            is_available=True,
        )
        session.add(off4)

        # 7. Field Officer 5 (BEST & Street Lighting - Worli Ward G/South)
        off_user5 = User(
            email="officer.lighting@civicpulse.gov.in",
            full_name="Anand Pawar",
            phone="+91 98200 22005",
            hashed_password=officer_pass,
            role=UserRole.OFFICER.value,
            is_active=True,
        )
        session.add(off_user5)
        session.flush()

        off5 = Officer(
            user_id=off_user5.id,
            department_id=dept_objs["DEPT_ELEC"].id,
            ward_id=ward_objs["Ward G/South (Worli, Lower Parel, Mahalaxmi)"].id,
            designation="Assistant Electrical Inspector (BEST Lighting)",
            employee_code="BEST-LGT-GS-033",
            is_available=True,
        )
        session.add(off5)

        # 8. Field Officer 6 (Public Health & Vector Control - Malad Ward P/North)
        off_user6 = User(
            email="officer.health@civicpulse.gov.in",
            full_name="Dr. Rupali Mane",
            phone="+91 98200 22006",
            hashed_password=officer_pass,
            role=UserRole.OFFICER.value,
            is_active=True,
        )
        session.add(off_user6)
        session.flush()

        off6 = Officer(
            user_id=off_user6.id,
            department_id=dept_objs["DEPT_HEALTH"].id,
            ward_id=ward_objs["Ward P/North (Malad West, Marve Road)"].id,
            designation="Medical Officer of Health (Ward P/North)",
            employee_code="BMC-MOH-PN-019",
            is_available=True,
        )
        session.add(off6)

        # 9. Field Officer 7 (Public Works Department - Malabar Hill Ward D)
        off_user7 = User(
            email="officer.pwd@civicpulse.gov.in",
            full_name="Sunil Joshi",
            phone="+91 98200 22007",
            hashed_password=officer_pass,
            role=UserRole.OFFICER.value,
            is_active=True,
        )
        session.add(off_user7)
        session.flush()

        off7 = Officer(
            user_id=off_user7.id,
            department_id=dept_objs["DEPT_PWD"].id,
            ward_id=ward_objs["Ward D (Malabar Hill, Walkeshwar, Girgaon)"].id,
            designation="Executive Engineer (PWD Civics, Ward D)",
            employee_code="BMC-PWD-D-071",
            is_available=True,
        )
        session.add(off7)


        # 6. Citizens
        citizen1 = User(
            email="citizen.rahul@example.com",
            full_name="Amit Deshmukh",
            phone="+91 98190 55001",
            hashed_password=citizen_pass,
            role=UserRole.CITIZEN.value,
            is_active=True,
        )
        session.add(citizen1)

        citizen2 = User(
            email="citizen.priya@example.com",
            full_name="Neha Kulkarni",
            phone="+91 98190 55002",
            hashed_password=citizen_pass,
            role=UserRole.CITIZEN.value,
            is_active=True,
        )
        session.add(citizen2)
        session.flush()

        logger.info("Seeding Sample Grievances & Status Lifecycles in Mumbai...")
        now = datetime.now(timezone.utc)

        # Sample 1: Pothole (In Progress)
        c1 = Complaint(
            complaint_number=generate_complaint_id(year=2026, sequence_num=101),
            citizen_id=citizen1.id,
            category_id=cat_objs["pothole"].id,
            department_id=dept_objs["DEPT_ROADS"].id,
            assigned_officer_id=off2.id,
            ward_id=ward_objs["Ward K/West (Andheri West, Juhu, Versova)"].id,
            title="Dangerous waterlogged pothole on Western Express Highway near Andheri Flyover",
            description="Massive 2ft crater on Western Express Highway (WEH) near Andheri flyover exit causing severe traffic jams and bike skids during evening monsoon rush.",
            severity=ComplaintSeverity.HIGH.value,
            status=ComplaintStatus.IN_PROGRESS.value,
            landmark="Opposite Andheri Metro Station, WEH Southbound",
            sla_deadline=now + timedelta(hours=18),
            created_at=now - timedelta(hours=6),
            is_escalated=False,
        )
        session.add(c1)
        session.flush()

        loc1 = ComplaintLocation(
            complaint_id=c1.id,
            latitude=19.1136,
            longitude=72.8664,
            address="Western Express Highway, Andheri East/West Junction, Mumbai",
            landmark="Near Andheri Flyover Exit",
            city="Mumbai",
            ward_name="Ward K/West",
            pincode="400058",
        )
        session.add(loc1)

        h1_1 = ComplaintStatusHistory(
            complaint_id=c1.id,
            from_status=None,
            to_status=ComplaintStatus.SUBMITTED.value,
            changed_by_id=citizen1.id,
            remarks="Grievance filed by citizen via mobile portal.",
            created_at=now - timedelta(hours=6),
        )
        h1_2 = ComplaintStatusHistory(
            complaint_id=c1.id,
            from_status=ComplaintStatus.SUBMITTED.value,
            to_status=ComplaintStatus.ASSIGNED.value,
            changed_by_id=off_user2.id,
            remarks="Assigned to Assistant Engineer Roads, Ward K/West.",
            created_at=now - timedelta(hours=4),
        )
        h1_3 = ComplaintStatusHistory(
            complaint_id=c1.id,
            from_status=ComplaintStatus.ASSIGNED.value,
            to_status=ComplaintStatus.IN_PROGRESS.value,
            changed_by_id=off_user2.id,
            remarks="Site inspected. BMC mastic asphalt repair truck dispatched for rapid overnight leveling.",
            created_at=now - timedelta(hours=2),
        )
        session.add_all([h1_1, h1_2, h1_3])

        ai1 = AIClassification(
            complaint_id=c1.id,
            suggested_severity="HIGH",
            confidence_score=0.94,
            summary_text="Deep pothole on high-traffic arterial corridor (Western Express Highway, Andheri). Mastic asphalt work underway.",
        )
        session.add(ai1)

        # Sample 2: Garbage Dump (Resolved)
        c2 = Complaint(
            complaint_number=generate_complaint_id(year=2026, sequence_num=102),
            citizen_id=citizen2.id,
            category_id=cat_objs["garbage"].id,
            department_id=dept_objs["DEPT_SWM"].id,
            assigned_officer_id=off1.id,
            ward_id=ward_objs["Ward H/West (Bandra West, Khar, Santacruz)"].id,
            title="Overflowing municipal community dumpster on Hill Road, Bandra West",
            description="The primary community collection dumpster on Hill Road near Mehboob Studio has not been cleared for 2 days. Stray animals scattering wet waste onto the road.",
            severity=ComplaintSeverity.MEDIUM.value,
            status=ComplaintStatus.RESOLVED.value,
            landmark="Near Mehboob Studio Junction, Hill Road",
            sla_deadline=now - timedelta(hours=10),
            created_at=now - timedelta(days=2),
            resolved_at=now - timedelta(hours=5),
            is_escalated=False,
        )
        session.add(c2)
        session.flush()

        loc2 = ComplaintLocation(
            complaint_id=c2.id,
            latitude=19.0596,
            longitude=72.8295,
            address="Hill Road, Bandra West, Mumbai",
            landmark="Near Mehboob Studio",
            city="Mumbai",
            ward_name="Ward H/West",
            pincode="400050",
        )
        session.add(loc2)

        h2_1 = ComplaintStatusHistory(
            complaint_id=c2.id,
            from_status=None,
            to_status=ComplaintStatus.SUBMITTED.value,
            changed_by_id=citizen2.id,
            remarks="Complaint registered by citizen.",
            created_at=now - timedelta(days=2),
        )
        h2_2 = ComplaintStatusHistory(
            complaint_id=c2.id,
            from_status=ComplaintStatus.SUBMITTED.value,
            to_status=ComplaintStatus.IN_PROGRESS.value,
            changed_by_id=off_user1.id,
            remarks="BMC SWM compactor truck deployed for immediate collection.",
            created_at=now - timedelta(days=1),
        )
        h2_3 = ComplaintStatusHistory(
            complaint_id=c2.id,
            from_status=ComplaintStatus.IN_PROGRESS.value,
            to_status=ComplaintStatus.RESOLVED.value,
            changed_by_id=off_user1.id,
            remarks="Dumpster cleared, surrounding pavement sanitized with disinfectant bleaching powder, and regular 2x daily pickup cycle restored.",
            created_at=now - timedelta(hours=5),
        )
        session.add_all([h2_1, h2_2, h2_3])

        # Sample 3: Water Leakage (Submitted / Fresh)
        c3 = Complaint(
            complaint_number=generate_complaint_id(year=2026, sequence_num=103),
            citizen_id=citizen1.id,
            category_id=cat_objs["water-leakage"].id,
            department_id=dept_objs["DEPT_BWSSB"].id,
            assigned_officer_id=off3.id,
            ward_id=ward_objs["Ward A (Colaba, Fort, Marine Drive)"].id,
            title="High-pressure potable water pipeline burst near Marine Drive promenade",
            description="Pressurized clean drinking water gushing out from an underground valve line near Churchgate. Thousands of liters of water spilling onto Netaji Subhash Chandra Bose Road.",
            severity=ComplaintSeverity.HIGH.value,
            status=ComplaintStatus.SUBMITTED.value,
            landmark="Opposite Hindu Gymkhana, Marine Drive Promenade",
            sla_deadline=now + timedelta(hours=20),
            created_at=now - timedelta(minutes=45),
            is_escalated=False,
        )
        session.add(c3)
        session.flush()

        loc3 = ComplaintLocation(
            complaint_id=c3.id,
            latitude=18.9426,
            longitude=72.8236,
            address="Netaji Subhash Chandra Bose Road, Marine Drive, Churchgate, Mumbai",
            landmark="Near Hindu Gymkhana, Marine Drive",
            city="Mumbai",
            ward_name="Ward A",
            pincode="400020",
        )
        session.add(loc3)

        h3_1 = ComplaintStatusHistory(
            complaint_id=c3.id,
            from_status=None,
            to_status=ComplaintStatus.SUBMITTED.value,
            changed_by_id=citizen1.id,
            remarks="Emergency potable pipeline burst reported by resident.",
            created_at=now - timedelta(minutes=45),
        )
        session.add(h3_1)

        # Notifications for demo users
        n1 = Notification(
            user_id=citizen1.id,
            complaint_id=c1.id,
            title="Field Work In Progress",
            message=f"BMC Roads repair team has commenced mastic asphalt patch work on your complaint {c1.complaint_number}.",
            channel=NotificationChannel.IN_APP.value,
            is_read=False,
        )
        n2 = Notification(
            user_id=citizen2.id,
            complaint_id=c2.id,
            title="Complaint Resolved ✅",
            message=f"Your complaint {c2.complaint_number} (Garbage Dumpster) has been successfully resolved by Ward H/West SWM team.",
            channel=NotificationChannel.IN_APP.value,
            is_read=False,
        )
        session.add_all([n1, n2])

        session.commit()
        logger.info("✅ Database seeded successfully with realistic Mumbai, Maharashtra civic dataset!")


if __name__ == "__main__":
    seed_database()
