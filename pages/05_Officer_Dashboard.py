"""Government Officer & Field Engineer Portal."""

import os
import sys
from pathlib import Path
import streamlit as st
import folium
from streamlit_folium import st_folium
from PIL import Image

# Setup Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.database import get_db_session
from backend.models.user import UserRole
from backend.models.complaint import ComplaintStatus, ComplaintSeverity
from backend.services.complaint_service import ComplaintService
from backend.services.sla_service import SLAService
from backend.services.storage_service import get_storage_provider
from backend.repositories.user_repo import UserRepository
from backend.repositories.category_repo import CategoryRepository
from backend.repositories.ward_repo import WardRepository
from backend.utils.formatting import format_status_badge, format_severity_badge, format_datetime
from backend.utils.session import init_session_state, get_current_user, require_auth, apply_custom_css
from backend.utils.icons import icon_svg

init_session_state()
apply_custom_css()

st.markdown(f'<h1 class="main-header">{icon_svg("hard-hat", size=28, color="#1E3A8A")} Government Officer Portal</h1>', unsafe_allow_html=True)

# RBAC Guard
if not require_auth(allowed_roles=[UserRole.OFFICER.value, UserRole.DEPARTMENT_ADMIN.value, UserRole.SUPER_ADMIN.value]):
    st.stop()

current_user = get_current_user()
officer_profile = current_user.get("officer_profile")
user_role = current_user.get("role")

with get_db_session() as session:
    comp_service = ComplaintService(session)
    sla_service = SLAService(session)
    user_repo = UserRepository(session)
    cat_repo = CategoryRepository(session)
    ward_repo = WardRepository(session)
    storage = get_storage_provider()

    # Department scope
    dept_id = officer_profile.get("department_id") if officer_profile else None
    officer_id = officer_profile.get("officer_id") if officer_profile else None

    # Header info
    st.info(
        f"Logged in: **{current_user['full_name']}** | Role: `{user_role}` | Department: **{officer_profile.get('department_name') if officer_profile else 'All (Admin)'}**"
    )

    if "officer_success_msg" in st.session_state and st.session_state["officer_success_msg"]:
        st.success(st.session_state["officer_success_msg"])
        del st.session_state["officer_success_msg"]

    # Top KPI Metrics
    dept_complaints = comp_service.list_complaints(department_id=dept_id if user_role != UserRole.SUPER_ADMIN.value else None)
    my_assigned = [c for c in dept_complaints if c.assigned_officer_id == officer_id] if officer_id else []

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Department Queue", len(dept_complaints))
    k2.metric("Assigned to Me", len(my_assigned))
    k3.metric("Action Required (Submitted)", sum(1 for c in dept_complaints if c.status == "SUBMITTED"), delta="Pending Triage")
    k4.metric("Overdue / At Risk", sum(1 for c in dept_complaints if c.is_escalated or sla_service.check_sla_status(c)["is_breached"]), delta_color="inverse")

    st.divider()

    # ── DETAIL / INSPECT WORKBENCH VIEW ───────────────────────────────────────
    inspect_id = st.session_state.get("officer_inspect_id")

    if inspect_id:
        complaint = comp_service.get_complaint_by_id(inspect_id)
        if not complaint:
            st.error("Complaint not found.")
            if st.button("⬅️ Return to Queue"):
                st.session_state.officer_inspect_id = None
                st.rerun()
        else:
            # Back Button & Header
            col_back_btn, _ = st.columns([1, 4])
            with col_back_btn:
                if st.button("⬅️ Back to Queue", use_container_width=True):
                    st.session_state.officer_inspect_id = None
                    st.rerun()

            st.markdown(f"## 🛠️ **{complaint.complaint_number}**: {complaint.title}")
            st.caption(f"Filed by **{complaint.citizen.full_name if complaint.citizen else 'Citizen'}** on {format_datetime(complaint.created_at)} | Status: {format_status_badge(complaint.status)} | Severity: {format_severity_badge(complaint.severity)}")

            # AI Briefing Box
            if complaint.ai_classification:
                ai = complaint.ai_classification
                st.markdown(
                    f"""
                    <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:10px; padding:14px; margin-bottom:14px;">
                        <span style="font-weight:bold; color:#1E40AF; font-size:1rem;">🤖 AI Field Summary & Briefing:</span><br>
                        <span style="font-size:0.92rem; color:#1E3A8A; line-height:1.5;">{ai.summary_text or 'Standard civic grievance.'}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            col_left, col_right = st.columns([1, 1])

            with col_left:
                st.markdown("#### 📍 **Location & Evidence**")
                st.write(f"**Citizen Description:** {complaint.description}")
                if complaint.location:
                    st.write(f"**Address:** {complaint.location.address}")
                    if complaint.location.landmark:
                        st.write(f"**Landmark:** {complaint.location.landmark}")

                    # Interactive Map
                    m_officer = folium.Map(location=[complaint.location.latitude, complaint.location.longitude], zoom_start=15)
                    folium.Marker(
                        [complaint.location.latitude, complaint.location.longitude],
                        popup=complaint.complaint_number,
                        tooltip=complaint.title,
                        icon=folium.Icon(color="red", icon="wrench"),
                    ).add_to(m_officer)
                    st_folium(m_officer, height=220, width=None, key="officer_map")

                # Attached Photos
                if complaint.media:
                    st.markdown("#### 📸 **Attached Media Proof**")
                    for med in complaint.media:
                        file_path = storage.get_file_path(med.storage_path)
                        if file_path and os.path.exists(file_path) and med.media_type == "image":
                            try:
                                img = Image.open(file_path)
                                st.image(img, caption=med.original_filename, use_container_width=True)
                            except Exception:
                                st.caption(f"📁 {med.original_filename}")
                        else:
                            st.caption(f"🎥 {med.original_filename} ({med.media_type.upper()})")

            with col_right:
                st.markdown("#### ⚡ **Officer Action & Status Transition**")

                status_choices = [
                    ComplaintStatus.ACKNOWLEDGED.value,
                    ComplaintStatus.WAITING_FOR_INFORMATION.value,
                    ComplaintStatus.IN_PROGRESS.value,
                    ComplaintStatus.RESOLVED.value,
                    ComplaintStatus.REJECTED.value,
                ]
                curr_status_idx = status_choices.index(complaint.status) if complaint.status in status_choices else 0

                new_status = st.selectbox("Update Lifecycle Status *", status_choices, index=curr_status_idx)
                officer_remarks = st.text_area(
                    "Action Remarks / Citizen Update *",
                    placeholder="e.g. Field inspection completed. Cleaning crew dispatched and waste cleared.",
                    height=100,
                )
                is_internal = st.checkbox("🔒 Mark as Internal Department Note (hidden from citizen)", value=False)

                # Resolution Proof Photo Uploader (Visible when status is RESOLVED)
                res_proof_file = None
                if new_status == ComplaintStatus.RESOLVED.value:
                    res_proof_file = st.file_uploader("📸 Upload Resolution Proof Photo (After Fix)", type=["jpg", "jpeg", "png", "webp"], key="res_proof_uploader")

                if st.button("💾 Apply Status Change & Notify Citizen", type="primary", use_container_width=True):
                    try:
                        clean_rem = officer_remarks.strip() or f"Status updated to {new_status} by municipal officer."

                        # If resolution proof uploaded, save media
                        if res_proof_file:
                            meta = storage.save_file(
                                file_bytes=res_proof_file.read(),
                                original_filename=res_proof_file.name,
                                content_type=res_proof_file.type,
                            )
                            comp_repo = comp_service.complaint_repo
                            comp_repo.add_media(
                                complaint_id=complaint.id,
                                file_name=meta["file_name"],
                                original_filename=f"Resolution Proof - {meta['original_filename']}",
                                file_size_bytes=meta["file_size_bytes"],
                                mime_type=meta["mime_type"],
                                storage_provider=meta["storage_provider"],
                                storage_path=meta["storage_path"],
                                file_hash=meta.get("file_hash"),
                                media_type=meta.get("media_type", "image"),
                            )

                        comp_service.update_status(
                            complaint_id=complaint.id,
                            user_id=current_user["user_id"],
                            to_status=ComplaintStatus(new_status),
                            remarks=clean_rem,
                            is_internal_note=is_internal,
                        )
                        session.commit()
                        st.session_state["officer_success_msg"] = f"🎉 Successfully updated **{complaint.complaint_number}** to **{new_status}**!"
                        st.session_state.officer_inspect_id = None
                        st.rerun()
                    except Exception as e:
                        session.rollback()
                        st.error(f"Error updating status: {e}")


                st.divider()

                # Reassign Officer Option
                st.markdown("#### 👤 **Officer Assignment**")
                dept_officers = user_repo.list_officers_by_department(complaint.department_id)
                officer_opts = {f"{o.designation} - {o.user.full_name} ({o.employee_code})": o.id for o in dept_officers if o.user}

                if officer_opts:
                    sel_officer_label = st.selectbox("Assign Field Officer", list(officer_opts.keys()))
                    assign_note = st.text_input("Assignment Note", placeholder="e.g. Urgent repair needed before monsoon peak")
                    if st.button("Reassign Officer"):
                        try:
                            comp_service.assign_to_officer(
                                complaint_id=complaint.id,
                                officer_id=officer_opts[sel_officer_label],
                                assigned_by_id=current_user["user_id"],
                                note=assign_note,
                            )
                            session.commit()
                            st.success("✅ Officer assigned successfully!")
                            st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"Error reassigning officer: {e}")

    # ── QUEUE LIST VIEW ───────────────────────────────────────────────────────
    else:
        tab_assigned, tab_dept, tab_completed = st.tabs([
            "🎯 Assigned to Me",
            "🏢 Active Department Queue",
            "✅ Completed & Resolved",
        ])

        with tab_assigned:
            st.markdown("### 🎯 **My Assigned Grievances**")
            active_my_assigned = [c for c in my_assigned if c.status not in ("RESOLVED", "REJECTED")]
            if not active_my_assigned:
                st.info("You currently have no pending complaints assigned directly to you.")
            else:
                for comp in active_my_assigned:
                    sla_badge = sla_service.check_sla_status(comp)["badge"]
                    with st.expander(f"**{comp.complaint_number}** - {comp.title} [{format_status_badge(comp.status)}] - {sla_badge}"):
                        c1, c2 = st.columns([2, 1])
                        with c1:
                            st.write(f"**Description:** {comp.description}")
                            st.write(f"📍 **Address:** {comp.location.address if comp.location else 'N/A'}")
                            st.write(f"⚡ **Severity:** {format_severity_badge(comp.severity)}")
                        with c2:
                            st.write(f"📅 **Date:** {format_datetime(comp.created_at)}")
                            if st.button("🔍 Open Grievance File", key=f"act_my_{comp.id}", type="primary"):
                                st.session_state.officer_inspect_id = comp.id
                                st.rerun()

        with tab_dept:
            st.markdown("### 🏢 **Active Department Queue & Filters**")

            f1, f2, f3 = st.columns(3)
            with f1:
                status_f = st.selectbox("Status", ["ALL ACTIVE", "SUBMITTED", "ACKNOWLEDGED", "ASSIGNED", "WAITING_FOR_INFORMATION", "IN_PROGRESS"])
            with f2:
                sev_f = st.selectbox("Severity", ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
            with f3:
                search_q = st.text_input("Search (ID or Keyword)")

            # Filter active queue
            active_queue = [c for c in dept_complaints if c.status not in ("RESOLVED", "REJECTED")]
            if status_f != "ALL ACTIVE":
                active_queue = [c for c in active_queue if c.status == status_f]
            if sev_f != "ALL":
                active_queue = [c for c in active_queue if c.severity == sev_f]
            if search_q:
                sq = search_q.lower()
                active_queue = [c for c in active_queue if sq in c.title.lower() or sq in c.complaint_number.lower() or sq in c.description.lower()]

            if not active_queue:
                st.info("No active grievances match the current filter. All caught up! 🎉")
            else:
                for comp in active_queue:
                    sla_info = sla_service.check_sla_status(comp)
                    with st.expander(f"**{comp.complaint_number}** | {comp.category.name if comp.category else ''} | {comp.title} | {format_status_badge(comp.status)} | {sla_info['badge']}"):
                        c1, c2, c3 = st.columns([2, 1, 1])
                        with c1:
                            st.write(f"**Citizen Description:** {comp.description}")
                            st.write(f"📍 **Location:** {comp.location.address if comp.location else settings.DEFAULT_CITY}")
                        with c2:
                            st.write(f"👤 **Assigned To:** {comp.assigned_officer.user.full_name if comp.assigned_officer and comp.assigned_officer.user else 'Unassigned'}")
                            st.write(f"⚡ **Priority:** {format_severity_badge(comp.severity)}")
                        with c3:
                            if st.button("🔍 Open Grievance File", key=f"open_{comp.id}", type="primary"):
                                st.session_state.officer_inspect_id = comp.id
                                st.rerun()

        with tab_completed:
            st.markdown("### ✅ **Completed & Resolved Grievances**")
            completed_list = [c for c in dept_complaints if c.status in ("RESOLVED", "REJECTED")]

            c_f1, c_f2 = st.columns([2, 1])
            with c_f1:
                search_comp = st.text_input("Search Completed Issues", placeholder="Filter by ID or keyword...", key="search_completed_input")
            with c_f2:
                st.metric("Total Resolved in Dept", len(completed_list))

            if search_comp:
                sq_comp = search_comp.lower()
                completed_list = [c for c in completed_list if sq_comp in c.title.lower() or sq_comp in c.complaint_number.lower() or sq_comp in c.description.lower()]

            if not completed_list:
                st.info("No completed grievances recorded yet for this department.")
            else:
                for comp in completed_list:
                    res_time_str = format_datetime(comp.resolved_at) if comp.resolved_at else "Resolved"
                    with st.expander(f"✔ **{comp.complaint_number}** | {comp.title} | {format_status_badge(comp.status)} | Closed on {res_time_str}"):
                        c1, c2, c3 = st.columns([2, 1, 1])
                        with c1:
                            st.write(f"**Problem:** {comp.description}")
                            st.write(f"📍 **Location:** {comp.location.address if comp.location else settings.DEFAULT_CITY}")
                            if comp.status_history:
                                latest_hist = comp.status_history[-1]
                                if latest_hist.remarks:
                                    st.info(f"📝 **Resolution Remarks:** {latest_hist.remarks}")
                        with c2:
                            st.write(f"👤 **Resolved By:** {comp.assigned_officer.user.full_name if comp.assigned_officer and comp.assigned_officer.user else 'Department Officer'}")
                            st.write(f"⚡ **Severity:** {format_severity_badge(comp.severity)}")
                            st.write(f"📸 **Media Count:** {len(comp.media)} file(s)")
                        with c3:
                            if st.button("🔍 View Full File", key=f"view_comp_{comp.id}", type="secondary"):
                                st.session_state.officer_inspect_id = comp.id
                                st.rerun()


