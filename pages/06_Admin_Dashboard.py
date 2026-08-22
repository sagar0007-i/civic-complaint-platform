"""Super Admin & Department Admin Management Console."""

import os
import sys
from pathlib import Path
import streamlit as st

# Setup Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.database import get_db_session
from backend.models.user import UserRole
from backend.services.auth_service import AuthService
from backend.services.audit_service import AuditService
from backend.repositories.department_repo import DepartmentRepository
from backend.repositories.ward_repo import WardRepository
from backend.repositories.category_repo import CategoryRepository
from backend.repositories.routing_repo import RoutingRepository
from backend.repositories.sla_repo import SLARepository
from backend.repositories.user_repo import UserRepository
from backend.utils.session import init_session_state, get_current_user, require_auth, apply_custom_css
from backend.utils.icons import icon_svg
from backend.utils.formatting import format_datetime

init_session_state()
apply_custom_css()

st.markdown(f'<h1 class="main-header">{icon_svg("building", size=28, color="#1E3A8A")} System Administration Console</h1>', unsafe_allow_html=True)

# RBAC Guard
if not require_auth(allowed_roles=[UserRole.SUPER_ADMIN.value, UserRole.DEPARTMENT_ADMIN.value]):
    st.stop()

current_user = get_current_user()
st.caption(f"Administrator: **{current_user['full_name']}** (`{current_user['role']}`)")

tab_depts, tab_wards, tab_cats, tab_routing, tab_sla, tab_users, tab_audit = st.tabs(
    [
        "🏢 Departments",
        "📍 Wards & Zones",
        "🗂️ Categories",
        "⚡ Routing Rules",
        "⏱️ SLA Rules",
        "👥 Users & Officers",
        "📜 Audit Logs",
    ]
)

with get_db_session() as session:
    dept_repo = DepartmentRepository(session)
    ward_repo = WardRepository(session)
    cat_repo = CategoryRepository(session)
    routing_repo = RoutingRepository(session)
    sla_repo = SLARepository(session)
    user_repo = UserRepository(session)
    audit_service = AuditService(session)
    auth_service = AuthService(session)

    # 1. DEPARTMENTS
    with tab_depts:
        st.markdown("### 🏢 **Municipal Departments**")
        depts = dept_repo.get_all(active_only=False)

        # Create department expander
        with st.expander("➕ Add New Civic Department"):
            with st.form("new_dept_form"):
                d_name = st.text_input("Department Name *", placeholder="e.g. Parks & Horticulture")
                d_code = st.text_input("Department Code *", placeholder="e.g. DEPT_PARKS")
                d_desc = st.text_area("Description", placeholder="Maintenance of public green spaces...")
                d_email = st.text_input("Contact Email", placeholder="parks@civicpulse.gov.in")
                d_submit = st.form_submit_button("Create Department", type="primary")

                if d_submit:
                    if not d_name or not d_code:
                        st.error("Name and Code are required.")
                    else:
                        try:
                            dept_repo.create(name=d_name, code=d_code, description=d_desc, contact_email=d_email)
                            session.commit()
                            st.success(f"Department '{d_name}' created!")
                            st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"Error: {e}")

        # List existing departments
        dept_data = [
            {"Name": d.name, "Code": d.code, "Email": d.contact_email or "-", "Active": "✅ Yes" if d.is_active else "❌ No"}
            for d in depts
        ]
        st.dataframe(dept_data, use_container_width=True)

    # 2. WARDS & ZONES
    with tab_wards:
        st.markdown("### 📍 **Municipal Wards & Geographic Zones**")
        wards = ward_repo.get_all(active_only=False)

        with st.expander("➕ Register New Ward / Locality"):
            with st.form("new_ward_form"):
                w_name = st.text_input("Ward Name *", placeholder="e.g. BTM Layout")
                w_num = st.number_input("Ward Number", min_value=1, max_value=999, value=176)
                w_zone = st.text_input("Zone *", placeholder="e.g. South Zone")
                w_pin = st.text_input("Pincode", placeholder="560076")
                w_lat = st.number_input("Center Latitude", value=12.9165, format="%.5f")
                w_lng = st.number_input("Center Longitude", value=77.6101, format="%.5f")
                w_submit = st.form_submit_button("Add Ward", type="primary")

                if w_submit:
                    if not w_name or not w_zone:
                        st.error("Ward Name and Zone are required.")
                    else:
                        try:
                            ward_repo.create(
                                name=w_name,
                                zone=w_zone,
                                ward_number=int(w_num),
                                pincode=w_pin,
                                center_lat=w_lat,
                                center_lng=w_lng,
                            )
                            session.commit()
                            st.success(f"Ward '{w_name}' added!")
                            st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"Error: {e}")

        ward_data = [
            {"Ward": w.name, "No.": w.ward_number, "Zone": w.zone, "City": w.city, "Pincode": w.pincode or "-"}
            for w in wards
        ]
        st.dataframe(ward_data, use_container_width=True)

    # 3. CATEGORIES
    with tab_cats:
        st.markdown("### 🗂️ **Complaint Categories**")
        cats = cat_repo.get_all(active_only=False)
        all_depts = dept_repo.get_all(active_only=True)
        dept_dict = {d.name: d.id for d in all_depts}

        with st.expander("➕ Add Complaint Category"):
            with st.form("new_cat_form"):
                c_name = st.text_input("Category Name *", placeholder="e.g. Stray Animal Rescue")
                c_slug = st.text_input("Category Slug *", placeholder="e.g. animal-rescue")
                c_icon = st.text_input("Icon Emoji", value="🐾")
                c_dept = st.selectbox("Default Department *", list(dept_dict.keys()))
                c_sev = st.selectbox("Default Severity", ["LOW", "MEDIUM", "HIGH", "CRITICAL"], index=1)
                c_submit = st.form_submit_button("Add Category", type="primary")

                if c_submit:
                    if not c_name or not c_slug:
                        st.error("Name and Slug are required.")
                    else:
                        try:
                            cat_repo.create(
                                name=c_name,
                                slug=c_slug,
                                department_id=dept_dict[c_dept],
                                icon=c_icon,
                                default_severity=c_sev,
                            )
                            session.commit()
                            st.success(f"Category '{c_name}' created!")
                            st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"Error: {e}")

        cat_data = [
            {"Category": f"{c.icon} {c.name}", "Slug": c.slug, "Department": c.department.name if c.department else "-", "Default Severity": c.default_severity}
            for c in cats
        ]
        st.dataframe(cat_data, use_container_width=True)

    # 4. ROUTING RULES
    with tab_routing:
        st.markdown("### ⚡ **Configurable Complaint Routing Rules**")
        rules = routing_repo.get_all(active_only=False)

        with st.expander("➕ Create Dynamic Routing Rule"):
            with st.form("new_rule_form"):
                r_name = st.text_input("Rule Name *", placeholder="e.g. Route Whitefield Sewage to BWSSB Mahadevapura")
                r_cat = st.selectbox("Category", [f"{c.icon} {c.name}" for c in cats])
                r_dept = st.selectbox("Target Department", list(dept_dict.keys()))
                r_prio = st.number_input("Priority Order (Lower = First)", min_value=1, max_value=100, value=10)
                r_submit = st.form_submit_button("Save Routing Rule", type="primary")

                if r_submit:
                    cat_obj = [c for c in cats if f"{c.icon} {c.name}" == r_cat][0]
                    routing_repo.create(
                        name=r_name,
                        category_id=cat_obj.id,
                        target_department_id=dept_dict[r_dept],
                        priority_order=int(r_prio),
                    )
                    session.commit()
                    st.success("Routing rule saved!")
                    st.rerun()

        rule_data = [
            {"Rule Name": r.name, "Category": r.category.name if r.category else "-", "Target Dept": r.target_department.name if r.target_department else "-", "Priority": r.priority_order}
            for r in rules
        ]
        st.dataframe(rule_data, use_container_width=True)

    # 5. SLA RULES
    with tab_sla:
        st.markdown("### ⏱️ **SLA & Escalation Thresholds**")
        slas = sla_repo.get_all(active_only=False)

        with st.expander("➕ Configure SLA Rule"):
            with st.form("new_sla_form"):
                s_name = st.text_input("SLA Name *", placeholder="e.g. Critical Flooding Rapid Response")
                s_sev = st.selectbox("Severity Level", ["(All Severities)", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
                s_resp = st.number_input("Target Acknowledge Hours", min_value=1, max_value=720, value=4)
                s_res = st.number_input("Target Resolution Hours", min_value=1, max_value=1440, value=12)
                s_role = st.selectbox("Escalate To", ["DEPARTMENT_ADMIN", "SUPER_ADMIN"])
                s_submit = st.form_submit_button("Save SLA Rule", type="primary")

                if s_submit:
                    sla_repo.create(
                        name=s_name,
                        severity=None if s_sev == "(All Severities)" else s_sev,
                        response_time_hours=int(s_resp),
                        resolution_time_hours=int(s_res),
                        escalation_role=s_role,
                    )
                    session.commit()
                    st.success("SLA rule saved!")
                    st.rerun()

        sla_data = [
            {"Rule Name": s.name, "Severity": s.severity or "Global", "Resp (Hrs)": s.response_time_hours, "Res (Hrs)": s.resolution_time_hours, "Escalation": s.escalation_role}
            for s in slas
        ]
        st.dataframe(sla_data, use_container_width=True)

    # 6. USERS & OFFICERS
    with tab_users:
        st.markdown("### 👥 **User Accounts & Field Officer Profiles**")
        users = user_repo.list_users(limit=50)

        with st.expander("➕ Create New Government Officer Account"):
            with st.form("new_officer_form"):
                o_name = st.text_input("Officer Full Name *", placeholder="e.g. Ramesh Babu")
                o_email = st.text_input("Official Email *", placeholder="ramesh.babu@civicpulse.gov.in")
                o_pass = st.text_input("Initial Password *", value="Officer@123", type="password")
                o_code = st.text_input("Employee / Badge ID *", placeholder="PWD-BLR-109")
                o_desig = st.text_input("Designation", value="Assistant Executive Engineer")
                o_dept = st.selectbox("Assigned Department *", list(dept_dict.keys()))
                o_submit = st.form_submit_button("Register Officer", type="primary")

                if o_submit:
                    u, err = auth_service.create_officer_account(
                        email=o_email,
                        full_name=o_name,
                        password=o_pass,
                        department_id=dept_dict[o_dept],
                        employee_code=o_code,
                        designation=o_desig,
                        admin_user_id=current_user["user_id"],
                    )
                    if err:
                        st.error(err)
                    else:
                        session.commit()
                        st.success(f"Officer account created for {o_name}!")
                        st.rerun()

        user_data = [
            {"Name": u.full_name, "Email": u.email, "Role": u.role, "Active": "✅" if u.is_active else "❌", "Joined": format_datetime(u.created_at)}
            for u in users
        ]
        st.dataframe(user_data, use_container_width=True)

    # 7. AUDIT LOGS
    with tab_audit:
        st.markdown("### 📜 **System Audit Logs & Regulatory Trails**")
        logs = audit_service.get_recent_logs(limit=50)

        log_data = [
            {"Timestamp": format_datetime(l.created_at), "Action": l.action, "Entity": f"{l.entity_type}:{l.entity_id}", "User ID": l.user_id or "Guest/System", "IP": l.ip_address or "-"}
            for l in logs
        ]
        st.dataframe(log_data, use_container_width=True)
