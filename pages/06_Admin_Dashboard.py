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

        # Check if we are currently editing a department
        editing_dept_id = st.session_state.get("editing_dept_id")
        if editing_dept_id:
            edit_dept_obj = dept_repo.get_by_id(editing_dept_id)
            if edit_dept_obj:
                st.markdown(f"#### ✏️ **Edit Department: {edit_dept_obj.name}**")
                with st.form("edit_dept_form"):
                    ed_name = st.text_input("Department Name *", value=edit_dept_obj.name)
                    ed_code = st.text_input("Department Code *", value=edit_dept_obj.code)
                    ed_desc = st.text_area("Description", value=edit_dept_obj.description or "")
                    ed_email = st.text_input("Contact Email", value=edit_dept_obj.contact_email or "")
                    ed_active = st.checkbox("Active", value=edit_dept_obj.is_active)

                    c1, c2 = st.columns([1, 1])
                    with c1:
                        ed_save = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                    with c2:
                        ed_cancel = st.form_submit_button("Cancel", use_container_width=True)

                if ed_cancel:
                    del st.session_state["editing_dept_id"]
                    st.rerun()

                elif ed_save:
                    if not ed_name or not ed_code:
                        st.error("Name and Code are required.")
                    else:
                        try:
                            # Check uniqueness
                            duplicate = dept_repo.get_by_code_exclude(ed_code, exclude_id=editing_dept_id)
                            if duplicate:
                                st.error("A department with this code already exists.")
                            else:
                                diffs = {}
                                if edit_dept_obj.name != ed_name: diffs["name"] = f"{edit_dept_obj.name} → {ed_name}"
                                if edit_dept_obj.code != ed_code: diffs["code"] = f"{edit_dept_obj.code} → {ed_code}"
                                if edit_dept_obj.description != ed_desc: diffs["description"] = f"{edit_dept_obj.description} → {ed_desc}"
                                if edit_dept_obj.contact_email != ed_email: diffs["contact_email"] = f"{edit_dept_obj.contact_email} → {ed_email}"
                                if edit_dept_obj.is_active != ed_active: diffs["is_active"] = f"{edit_dept_obj.is_active} → {ed_active}"

                                dept_repo.update(
                                    dept_id=editing_dept_id,
                                    name=ed_name,
                                    code=ed_code,
                                    description=ed_desc if ed_desc else None,
                                    contact_email=ed_email if ed_email else None,
                                    is_active=ed_active,
                                )

                                audit_service.log_event(
                                    action="UPDATE_DEPARTMENT",
                                    entity_type="Department",
                                    entity_id=editing_dept_id,
                                    user_id=current_user["user_id"],
                                    details={"changes": diffs, "dept_name": ed_name}
                                )

                                session.commit()
                                st.success("Department updated successfully.")
                                del st.session_state["editing_dept_id"]
                                st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"Error: {e}")

        else:
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
        st.markdown("#### **Existing Civic Departments**")
        col_header = st.columns([3, 2, 3, 2, 2])
        with col_header[0]: st.markdown("**Name**")
        with col_header[1]: st.markdown("**Code**")
        with col_header[2]: st.markdown("**Email**")
        with col_header[3]: st.markdown("**Status**")
        with col_header[4]: st.markdown("**Actions**")
        st.divider()

        for d in depts:
            col_row = st.columns([3, 2, 3, 2, 2])
            with col_row[0]: st.write(d.name)
            with col_row[1]: st.write(d.code)
            with col_row[2]: st.write(d.contact_email or "-")
            with col_row[3]: st.write("✅ Active" if d.is_active else "❌ Inactive")
            with col_row[4]:
                if st.button("✏️ Edit", key=f"btn_edit_dept_{d.id}"):
                    st.session_state["editing_dept_id"] = d.id
                    st.rerun()

    # 2. WARDS & ZONES
    with tab_wards:
        st.markdown("### 📍 **Municipal Wards & Geographic Zones**")
        wards = ward_repo.get_all(active_only=False)

        # Check if we are currently editing a ward
        editing_id = st.session_state.get("editing_ward_id")
        if editing_id:
            edit_ward_obj = ward_repo.get_by_id(editing_id)
            if edit_ward_obj:
                st.markdown(f"#### ✏️ **Edit Ward / Locality: {edit_ward_obj.name}**")
                with st.form("edit_ward_form"):
                    ew_name = st.text_input("Ward Name *", value=edit_ward_obj.name)
                    ew_num = st.number_input("Ward Number *", min_value=1, max_value=999, value=int(edit_ward_obj.ward_number or 1))
                    ew_zone = st.text_input("Zone *", value=edit_ward_obj.zone)
                    ew_city = st.text_input("City *", value=edit_ward_obj.city)
                    ew_pin = st.text_input("Pincode", value=edit_ward_obj.pincode or "")
                    ew_lat = st.number_input("Center Latitude", value=float(edit_ward_obj.center_latitude or 0.0), format="%.5f")
                    ew_lng = st.number_input("Center Longitude", value=float(edit_ward_obj.center_longitude or 0.0), format="%.5f")
                    ew_active = st.checkbox("Active", value=edit_ward_obj.is_active)

                    c1, c2 = st.columns([1, 1])
                    with c1:
                        ew_save = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                    with c2:
                        ew_cancel = st.form_submit_button("Cancel", use_container_width=True)

                if ew_cancel:
                    del st.session_state["editing_ward_id"]
                    st.rerun()

                elif ew_save:
                    if not ew_name or not ew_zone or not ew_city:
                        st.error("Ward Name, Zone, and City are required.")
                    else:
                        from backend.schemas.department import WardCreateSchema
                        from pydantic import ValidationError
                        try:
                            # Validate using Pydantic schema
                            WardCreateSchema(
                                name=ew_name,
                                ward_number=int(ew_num),
                                zone=ew_zone,
                                city=ew_city,
                                pincode=ew_pin if ew_pin else None,
                                center_latitude=ew_lat,
                                center_longitude=ew_lng,
                            )

                            # Uniqueness constraint check (Ward No + Zone)
                            duplicate = ward_repo.get_by_number_and_zone(int(ew_num), ew_zone, exclude_id=editing_id)
                            if duplicate:
                                st.error("A ward with this number already exists in this zone.")
                            else:
                                # Track differences for audit log
                                diffs = {}
                                if edit_ward_obj.name != ew_name:
                                    diffs["name"] = f"{edit_ward_obj.name} → {ew_name}"
                                if edit_ward_obj.ward_number != int(ew_num):
                                    diffs["ward_number"] = f"{edit_ward_obj.ward_number} → {ew_num}"
                                if edit_ward_obj.zone != ew_zone:
                                    diffs["zone"] = f"{edit_ward_obj.zone} → {ew_zone}"
                                if edit_ward_obj.city != ew_city:
                                    diffs["city"] = f"{edit_ward_obj.city} → {ew_city}"
                                if edit_ward_obj.pincode != ew_pin:
                                    diffs["pincode"] = f"{edit_ward_obj.pincode} → {ew_pin}"
                                if edit_ward_obj.center_latitude != ew_lat:
                                    diffs["center_latitude"] = f"{edit_ward_obj.center_latitude} → {ew_lat}"
                                if edit_ward_obj.center_longitude != ew_lng:
                                    diffs["center_longitude"] = f"{edit_ward_obj.center_longitude} → {ew_lng}"
                                if edit_ward_obj.is_active != ew_active:
                                    diffs["is_active"] = f"{edit_ward_obj.is_active} → {ew_active}"

                                # Save changes
                                ward_repo.update(
                                    ward_id=editing_id,
                                    name=ew_name,
                                    zone=ew_zone,
                                    ward_number=int(ew_num),
                                    city=ew_city,
                                    pincode=ew_pin if ew_pin else None,
                                    center_lat=ew_lat,
                                    center_lng=ew_lng,
                                    is_active=ew_active,
                                )

                                # Log audit event
                                audit_service.log_event(
                                    action="UPDATE_WARD",
                                    entity_type="Ward",
                                    entity_id=editing_id,
                                    user_id=current_user["user_id"],
                                    details={"changes": diffs, "ward_name": ew_name}
                                )

                                session.commit()
                                st.success("Ward updated successfully.")
                                del st.session_state["editing_ward_id"]
                                st.rerun()
                        except ValidationError as ve:
                            st.error(f"Validation Error: {ve.errors()[0]['msg']}")
                        except Exception as e:
                            session.rollback()
                            st.error(f"Error: {e}")

        # Regular registration expander (only shown when not editing to keep screen clean)
        else:
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
                            from backend.schemas.department import WardCreateSchema
                            from pydantic import ValidationError
                            try:
                                # Validate new ward details
                                WardCreateSchema(
                                    name=w_name,
                                    ward_number=int(w_num),
                                    zone=w_zone,
                                    pincode=w_pin if w_pin else None,
                                    center_latitude=w_lat,
                                    center_longitude=w_lng,
                                )

                                # Uniqueness constraint check (Ward No + Zone)
                                duplicate = ward_repo.get_by_number_and_zone(int(w_num), w_zone)
                                if duplicate:
                                    st.error("A ward with this number already exists in this zone.")
                                else:
                                    new_ward = ward_repo.create(
                                        name=w_name,
                                        zone=w_zone,
                                        ward_number=int(w_num),
                                        pincode=w_pin if w_pin else None,
                                        center_lat=w_lat,
                                        center_lng=w_lng,
                                    )
                                    
                                    # Audit log for creation
                                    audit_service.log_event(
                                        action="CREATE_WARD",
                                        entity_type="Ward",
                                        entity_id=new_ward.id,
                                        user_id=current_user["user_id"],
                                        details={"ward_name": w_name, "zone": w_zone, "ward_number": int(w_num)}
                                    )

                                    session.commit()
                                    st.success(f"Ward '{w_name}' added!")
                                    st.rerun()
                            except ValidationError as ve:
                                st.error(f"Validation Error: {ve.errors()[0]['msg']}")
                            except Exception as e:
                                session.rollback()
                                st.error(f"Error: {e}")

        # List existing wards
        st.markdown("#### **Existing Wards & Zones**")
        col_header = st.columns([2.5, 1, 2, 1.2, 1.3, 1, 1])
        with col_header[0]: st.markdown("**Ward**")
        with col_header[1]: st.markdown("**No.**")
        with col_header[2]: st.markdown("**Zone**")
        with col_header[3]: st.markdown("**City**")
        with col_header[4]: st.markdown("**Pincode**")
        with col_header[5]: st.markdown("**Status**")
        with col_header[6]: st.markdown("**Actions**")
        st.divider()

        for w in wards:
            col_row = st.columns([2.5, 1, 2, 1.2, 1.3, 1, 1])
            with col_row[0]: st.write(w.name)
            with col_row[1]: st.write(str(w.ward_number or "-"))
            with col_row[2]: st.write(w.zone)
            with col_row[3]: st.write(w.city)
            with col_row[4]: st.write(w.pincode or "-")
            with col_row[5]: st.write("✅ Active" if w.is_active else "❌ Inactive")
            with col_row[6]:
                if st.button("✏️ Edit", key=f"btn_edit_{w.id}"):
                    st.session_state["editing_ward_id"] = w.id
                    st.rerun()


    # 3. CATEGORIES
    with tab_cats:
        st.markdown("### 🗂️ **Complaint Categories**")
        cats = cat_repo.get_all(active_only=False)
        all_depts = dept_repo.get_all(active_only=True)
        dept_dict = {d.name: d.id for d in all_depts}

        # Check if we are currently editing a category
        editing_cat_id = st.session_state.get("editing_cat_id")
        if editing_cat_id:
            edit_cat_obj = cat_repo.get_by_id(editing_cat_id)
            if edit_cat_obj:
                st.markdown(f"#### ✏️ **Edit Complaint Category: {edit_cat_obj.name}**")
                # Find default selectbox index for department and severity
                dept_names = list(dept_dict.keys())
                current_dept_name = edit_cat_obj.department.name if edit_cat_obj.department else None
                dept_index = dept_names.index(current_dept_name) if current_dept_name in dept_names else 0
                
                sev_options = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                sev_index = sev_options.index(edit_cat_obj.default_severity) if edit_cat_obj.default_severity in sev_options else 1
                
                with st.form("edit_cat_form"):
                    ec_name = st.text_input("Category Name *", value=edit_cat_obj.name)
                    ec_slug = st.text_input("Category Slug *", value=edit_cat_obj.slug)
                    ec_icon = st.text_input("Icon Emoji", value=edit_cat_obj.icon)
                    ec_dept = st.selectbox("Default Department *", dept_names, index=dept_index)
                    ec_sev = st.selectbox("Default Severity", sev_options, index=sev_index)
                    ec_active = st.checkbox("Active", value=edit_cat_obj.is_active)

                    c1, c2 = st.columns([1, 1])
                    with c1:
                        ec_save = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                    with c2:
                        ec_cancel = st.form_submit_button("Cancel", use_container_width=True)

                if ec_cancel:
                    del st.session_state["editing_cat_id"]
                    st.rerun()

                elif ec_save:
                    if not ec_name or not ec_slug:
                        st.error("Name and Slug are required.")
                    else:
                        from backend.schemas.department import CategoryCreateSchema
                        from pydantic import ValidationError
                        try:
                            # Validate using CategoryCreateSchema
                            CategoryCreateSchema(
                                name=ec_name,
                                slug=ec_slug,
                                department_id=dept_dict[ec_dept],
                                icon=ec_icon,
                                default_severity=ec_sev,
                            )
                            # Check uniqueness
                            duplicate = cat_repo.get_by_slug_exclude(ec_slug, exclude_id=editing_cat_id)
                            if duplicate:
                                st.error("A category with this slug already exists.")
                            else:
                                diffs = {}
                                if edit_cat_obj.name != ec_name: diffs["name"] = f"{edit_cat_obj.name} → {ec_name}"
                                if edit_cat_obj.slug != ec_slug: diffs["slug"] = f"{edit_cat_obj.slug} → {ec_slug}"
                                if edit_cat_obj.icon != ec_icon: diffs["icon"] = f"{edit_cat_obj.icon} → {ec_icon}"
                                if edit_cat_obj.department_id != dept_dict[ec_dept]: diffs["department_id"] = f"{edit_cat_obj.department_id} → {dept_dict[ec_dept]}"
                                if edit_cat_obj.default_severity != ec_sev: diffs["default_severity"] = f"{edit_cat_obj.default_severity} → {ec_sev}"
                                if edit_cat_obj.is_active != ec_active: diffs["is_active"] = f"{edit_cat_obj.is_active} → {ec_active}"

                                cat_repo.update(
                                    cat_id=editing_cat_id,
                                    name=ec_name,
                                    slug=ec_slug,
                                    department_id=dept_dict[ec_dept],
                                    icon=ec_icon,
                                    default_severity=ec_sev,
                                    is_active=ec_active,
                                )

                                audit_service.log_event(
                                    action="UPDATE_CATEGORY",
                                    entity_type="ComplaintCategory",
                                    entity_id=editing_cat_id,
                                    user_id=current_user["user_id"],
                                    details={"changes": diffs, "category_name": ec_name}
                                )

                                session.commit()
                                st.success("Category updated successfully.")
                                del st.session_state["editing_cat_id"]
                                st.rerun()
                        except ValidationError as ve:
                            st.error(f"Validation Error: {ve.errors()[0]['msg']}")
                        except Exception as e:
                            session.rollback()
                            st.error(f"Error: {e}")

        else:
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

        # List existing categories
        st.markdown("#### **Existing Complaint Categories**")
        col_header = st.columns([3, 2, 3, 2, 2, 2])
        with col_header[0]: st.markdown("**Category**")
        with col_header[1]: st.markdown("**Slug**")
        with col_header[2]: st.markdown("**Department**")
        with col_header[3]: st.markdown("**Severity**")
        with col_header[4]: st.markdown("**Status**")
        with col_header[5]: st.markdown("**Actions**")
        st.divider()

        for c in cats:
            col_row = st.columns([3, 2, 3, 2, 2, 2])
            with col_row[0]: st.write(f"{c.icon} {c.name}")
            with col_row[1]: st.write(c.slug)
            with col_row[2]: st.write(c.department.name if c.department else "-")
            with col_row[3]: st.write(c.default_severity)
            with col_row[4]: st.write("✅ Active" if c.is_active else "❌ Inactive")
            with col_row[5]:
                if st.button("✏️ Edit", key=f"btn_edit_cat_{c.id}"):
                    st.session_state["editing_cat_id"] = c.id
                    st.rerun()

    # 4. ROUTING RULES
    with tab_routing:
        st.markdown("### ⚡ **Configurable Complaint Routing Rules**")
        rules = routing_repo.get_all(active_only=False)

        # Check if we are currently editing a routing rule
        editing_rule_id = st.session_state.get("editing_rule_id")
        if editing_rule_id:
            from backend.models.routing import RoutingRule
            edit_rule_obj = session.query(RoutingRule).filter(RoutingRule.id == editing_rule_id).first()
            if edit_rule_obj:
                st.markdown(f"#### ✏️ **Edit Routing Rule: {edit_rule_obj.name}**")
                
                cat_names = [f"{c.icon} {c.name}" for c in cats]
                current_cat_name = f"{edit_rule_obj.category.icon} {edit_rule_obj.category.name}" if edit_rule_obj.category else None
                cat_index = cat_names.index(current_cat_name) if current_cat_name in cat_names else 0
                
                dept_names = list(dept_dict.keys())
                current_dept_name = edit_rule_obj.target_department.name if edit_rule_obj.target_department else None
                dept_index = dept_names.index(current_dept_name) if current_dept_name in dept_names else 0
                
                with st.form("edit_rule_form"):
                    er_name = st.text_input("Rule Name *", value=edit_rule_obj.name)
                    er_cat = st.selectbox("Category", cat_names, index=cat_index)
                    er_dept = st.selectbox("Target Department", dept_names, index=dept_index)
                    er_prio = st.number_input("Priority Order (Lower = First)", min_value=1, max_value=100, value=int(edit_rule_obj.priority_order))
                    er_active = st.checkbox("Active", value=edit_rule_obj.is_active)

                    c1, c2 = st.columns([1, 1])
                    with c1:
                        er_save = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                    with c2:
                        er_cancel = st.form_submit_button("Cancel", use_container_width=True)

                if er_cancel:
                    del st.session_state["editing_rule_id"]
                    st.rerun()

                elif er_save:
                    if not er_name:
                        st.error("Rule Name is required.")
                    else:
                        try:
                            cat_obj = [c for c in cats if f"{c.icon} {c.name}" == er_cat][0]
                            diffs = {}
                            if edit_rule_obj.name != er_name: diffs["name"] = f"{edit_rule_obj.name} → {er_name}"
                            if edit_rule_obj.category_id != cat_obj.id: diffs["category_id"] = f"{edit_rule_obj.category_id} → {cat_obj.id}"
                            if edit_rule_obj.target_department_id != dept_dict[er_dept]: diffs["target_department_id"] = f"{edit_rule_obj.target_department_id} → {dept_dict[er_dept]}"
                            if edit_rule_obj.priority_order != int(er_prio): diffs["priority_order"] = f"{edit_rule_obj.priority_order} → {er_prio}"
                            if edit_rule_obj.is_active != er_active: diffs["is_active"] = f"{edit_rule_obj.is_active} → {er_active}"

                            routing_repo.update(
                                rule_id=editing_rule_id,
                                name=er_name,
                                category_id=cat_obj.id,
                                target_department_id=dept_dict[er_dept],
                                priority_order=int(er_prio),
                                is_active=er_active,
                            )

                            audit_service.log_event(
                                action="UPDATE_ROUTING_RULE",
                                entity_type="RoutingRule",
                                entity_id=editing_rule_id,
                                user_id=current_user["user_id"],
                                details={"changes": diffs, "rule_name": er_name}
                            )

                            session.commit()
                            st.success("Routing rule updated successfully.")
                            del st.session_state["editing_rule_id"]
                            st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"Error: {e}")

        else:
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

        # List existing routing rules
        st.markdown("#### **Existing Routing Rules**")
        col_header = st.columns([3, 2, 3, 1.5, 1.5, 1.5])
        with col_header[0]: st.markdown("**Rule Name**")
        with col_header[1]: st.markdown("**Category**")
        with col_header[2]: st.markdown("**Target Department**")
        with col_header[3]: st.markdown("**Priority**")
        with col_header[4]: st.markdown("**Status**")
        with col_header[5]: st.markdown("**Actions**")
        st.divider()

        for r in rules:
            col_row = st.columns([3, 2, 3, 1.5, 1.5, 1.5])
            with col_row[0]: st.write(r.name)
            with col_row[1]: st.write(r.category.name if r.category else "-")
            with col_row[2]: st.write(r.target_department.name if r.target_department else "-")
            with col_row[3]: st.write(str(r.priority_order))
            with col_row[4]: st.write("✅ Active" if r.is_active else "❌ Inactive")
            with col_row[5]:
                if st.button("✏️ Edit", key=f"btn_edit_rule_{r.id}"):
                    st.session_state["editing_rule_id"] = r.id
                    st.rerun()

    # 5. SLA RULES
    with tab_sla:
        st.markdown("### ⏱️ **SLA & Escalation Thresholds**")
        slas = sla_repo.get_all(active_only=False)

        # Check if we are currently editing an SLA rule
        editing_sla_id = st.session_state.get("editing_sla_id")
        if editing_sla_id:
            edit_sla_obj = sla_repo.get_by_id(editing_sla_id)
            if edit_sla_obj:
                st.markdown(f"#### ✏️ **Edit SLA Rule: {edit_sla_obj.name}**")
                
                sev_options = ["(All Severities)", "CRITICAL", "HIGH", "MEDIUM", "LOW"]
                current_sev = edit_sla_obj.severity if edit_sla_obj.severity else "(All Severities)"
                sev_index = sev_options.index(current_sev) if current_sev in sev_options else 0
                
                esc_options = ["DEPARTMENT_ADMIN", "SUPER_ADMIN"]
                esc_index = esc_options.index(edit_sla_obj.escalation_role) if edit_sla_obj.escalation_role in esc_options else 0
                
                with st.form("edit_sla_form"):
                    es_name = st.text_input("SLA Name *", value=edit_sla_obj.name)
                    es_sev = st.selectbox("Severity Level", sev_options, index=sev_index)
                    es_resp = st.number_input("Target Acknowledge Hours", min_value=1, max_value=720, value=int(edit_sla_obj.response_time_hours))
                    es_res = st.number_input("Target Resolution Hours", min_value=1, max_value=1440, value=int(edit_sla_obj.resolution_time_hours))
                    es_role = st.selectbox("Escalate To", esc_options, index=esc_index)
                    es_active = st.checkbox("Active", value=edit_sla_obj.is_active)

                    c1, c2 = st.columns([1, 1])
                    with c1:
                        es_save = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                    with c2:
                        es_cancel = st.form_submit_button("Cancel", use_container_width=True)

                if es_cancel:
                    del st.session_state["editing_sla_id"]
                    st.rerun()

                elif es_save:
                    if not es_name:
                        st.error("SLA Name is required.")
                    else:
                        try:
                            diffs = {}
                            if edit_sla_obj.name != es_name: diffs["name"] = f"{edit_sla_obj.name} → {es_name}"
                            target_sev = None if es_sev == "(All Severities)" else es_sev
                            if edit_sla_obj.severity != target_sev: diffs["severity"] = f"{edit_sla_obj.severity} → {target_sev}"
                            if edit_sla_obj.response_time_hours != int(es_resp): diffs["response_time_hours"] = f"{edit_sla_obj.response_time_hours} → {es_resp}"
                            if edit_sla_obj.resolution_time_hours != int(es_res): diffs["resolution_time_hours"] = f"{edit_sla_obj.resolution_time_hours} → {es_res}"
                            if edit_sla_obj.escalation_role != es_role: diffs["escalation_role"] = f"{edit_sla_obj.escalation_role} → {es_role}"
                            if edit_sla_obj.is_active != es_active: diffs["is_active"] = f"{edit_sla_obj.is_active} → {es_active}"

                            sla_repo.update(
                                sla_id=editing_sla_id,
                                name=es_name,
                                severity=target_sev,
                                response_time_hours=int(es_resp),
                                resolution_time_hours=int(es_res),
                                escalation_role=es_role,
                                is_active=es_active,
                            )

                            audit_service.log_event(
                                action="UPDATE_SLA_RULE",
                                entity_type="SLARule",
                                entity_id=editing_sla_id,
                                user_id=current_user["user_id"],
                                details={"changes": diffs, "sla_name": es_name}
                            )

                            session.commit()
                            st.success("SLA rule updated successfully.")
                            del st.session_state["editing_sla_id"]
                            st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"Error: {e}")

        else:
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

        # List existing SLA rules
        st.markdown("#### **Existing SLA Rules**")
        col_header = st.columns([3, 2, 2, 2, 2, 2, 2])
        with col_header[0]: st.markdown("**Rule Name**")
        with col_header[1]: st.markdown("**Severity**")
        with col_header[2]: st.markdown("**Ack (Hrs)**")
        with col_header[3]: st.markdown("**Res (Hrs)**")
        with col_header[4]: st.markdown("**Escalation**")
        with col_header[5]: st.markdown("**Status**")
        with col_header[6]: st.markdown("**Actions**")
        st.divider()

        for s in slas:
            col_row = st.columns([3, 2, 2, 2, 2, 2, 2])
            with col_row[0]: st.write(s.name)
            with col_row[1]: st.write(s.severity or "Global")
            with col_row[2]: st.write(str(s.response_time_hours))
            with col_row[3]: st.write(str(s.resolution_time_hours))
            with col_row[4]: st.write(s.escalation_role)
            with col_row[5]: st.write("✅ Active" if s.is_active else "❌ Inactive")
            with col_row[6]:
                if st.button("✏️ Edit", key=f"btn_edit_sla_{s.id}"):
                    st.session_state["editing_sla_id"] = s.id
                    st.rerun()

    # 6. USERS & OFFICERS
    with tab_users:
        st.markdown("### 👥 **User Accounts & Field Officer Profiles**")
        users = user_repo.list_users(limit=50)

        # Check if we are currently editing a user
        editing_user_id = st.session_state.get("editing_user_id")
        if editing_user_id:
            edit_user_obj = user_repo.get_by_id(editing_user_id)
            if edit_user_obj:
                st.markdown(f"#### ✏️ **Edit User Profile: {edit_user_obj.full_name}**")
                
                role_options = ["CITIZEN", "OFFICER", "DEPT_ADMIN", "SUPER_ADMIN"]
                role_index = role_options.index(edit_user_obj.role) if edit_user_obj.role in role_options else 0
                
                with st.form("edit_user_form"):
                    eu_name = st.text_input("Full Name *", value=edit_user_obj.full_name)
                    eu_email = st.text_input("Email Address *", value=edit_user_obj.email)
                    eu_role = st.selectbox("Role *", role_options, index=role_index)
                    eu_active = st.checkbox("Active", value=edit_user_obj.is_active)

                    c1, c2 = st.columns([1, 1])
                    with c1:
                        eu_save = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                    with c2:
                        eu_cancel = st.form_submit_button("Cancel", use_container_width=True)

                if eu_cancel:
                    del st.session_state["editing_user_id"]
                    st.rerun()

                elif eu_save:
                    if not eu_name or not eu_email:
                        st.error("Full Name and Email Address are required.")
                    else:
                        try:
                            # Call the backend method with security validation guards
                            updated_user, err = user_repo.update_user(
                                user_id=editing_user_id,
                                full_name=eu_name,
                                email=eu_email,
                                role=eu_role,
                                is_active=eu_active,
                                caller_id=current_user["user_id"],
                            )
                            if err:
                                st.error(err)
                            else:
                                diffs = {}
                                if edit_user_obj.full_name != eu_name: diffs["full_name"] = f"{edit_user_obj.full_name} → {eu_name}"
                                if edit_user_obj.email != eu_email: diffs["email"] = f"{edit_user_obj.email} → {eu_email}"
                                if edit_user_obj.role != eu_role: diffs["role"] = f"{edit_user_obj.role} → {eu_role}"
                                if edit_user_obj.is_active != eu_active: diffs["is_active"] = f"{edit_user_obj.is_active} → {eu_active}"

                                audit_service.log_event(
                                    action="UPDATE_USER",
                                    entity_type="User",
                                    entity_id=editing_user_id,
                                    user_id=current_user["user_id"],
                                    details={"changes": diffs, "user_email": eu_email}
                                )

                                session.commit()
                                st.success("User profile updated successfully.")
                                del st.session_state["editing_user_id"]
                                st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"Error: {e}")

        else:
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

        # List existing users
        st.markdown("#### **Existing Users & Officers**")
        col_header = st.columns([3, 3, 2, 2, 2, 2])
        with col_header[0]: st.markdown("**Name**")
        with col_header[1]: st.markdown("**Email**")
        with col_header[2]: st.markdown("**Role**")
        with col_header[3]: st.markdown("**Status**")
        with col_header[4]: st.markdown("**Joined**")
        with col_header[5]: st.markdown("**Actions**")
        st.divider()

        for u in users:
            col_row = st.columns([3, 3, 2, 2, 2, 2])
            with col_row[0]: st.write(u.full_name)
            with col_row[1]: st.write(u.email)
            with col_row[2]: st.write(u.role)
            with col_row[3]: st.write("✅ Active" if u.is_active else "❌ Inactive")
            with col_row[4]: st.write(format_datetime(u.created_at))
            with col_row[5]:
                if st.button("✏️ Edit", key=f"btn_edit_user_{u.id}"):
                    st.session_state["editing_user_id"] = u.id
                    st.rerun()

    # 7. AUDIT LOGS
    with tab_audit:
        st.markdown("### 📜 **System Audit Logs & Regulatory Trails**")
        logs = audit_service.get_recent_logs(limit=50)

        log_data = [
            {"Timestamp": format_datetime(l.created_at), "Action": l.action, "Entity": f"{l.entity_type}:{l.entity_id}", "User ID": l.user_id or "Guest/System", "IP": l.ip_address or "-"}
            for l in logs
        ]
        st.dataframe(log_data, use_container_width=True)
