"""Civic Complaint Tracking Portal with Live Status Timeline & Interactive Map."""

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

from backend.config import settings
from backend.database import get_db_session
from backend.services.complaint_service import ComplaintService
from backend.services.sla_service import SLAService
from backend.services.storage_service import get_storage_provider
from backend.utils.formatting import format_status_badge, format_severity_badge, format_datetime
from backend.utils.session import init_session_state, get_current_user, is_logged_in, apply_custom_css

init_session_state()
apply_custom_css()

st.markdown('<h1 class="main-header">🔍 Track Complaint Status</h1>', unsafe_allow_html=True)
st.caption("Enter your unique Complaint ID to check real-time field progress, department responses, and timeline updates.")

# Prefill from session if redirected from submission
default_search = st.session_state.get("search_complaint_num", "")

search_col1, search_col2 = st.columns([3, 1])
with search_col1:
    search_input = st.text_input(
        "Enter Complaint Number",
        value=default_search,
        placeholder="e.g. CIV-2026-000101",
        label_visibility="collapsed",
    )
with search_col2:
    search_btn = st.button("Search Status", type="primary", use_container_width=True)

complaint_to_display = None

with get_db_session() as session:
    comp_service = ComplaintService(session)
    sla_service = SLAService(session)
    storage = get_storage_provider()

    if search_input or default_search:
        target_num = search_input.strip() if search_input else default_search.strip()
        complaint_to_display = comp_service.get_complaint_by_number(target_num)
        if not complaint_to_display:
            st.error(f"❌ No complaint found matching ID: **{target_num}**. Please verify the number.")

    # If no search, show a list of recent complaints to click & inspect
    if not complaint_to_display:
        st.markdown("### 📋 **Recent Public Grievances**")
        recent = comp_service.list_complaints(limit=6)
        if recent:
            cols = st.columns(3)
            for idx, c in enumerate(recent):
                with cols[idx % 3]:
                    st.markdown(
                        f"""
                        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px; margin-bottom:10px;">
                            <span style="font-weight:bold; color:#1E3A8A;">{c.complaint_number}</span><br>
                            <span style="font-size:0.9rem; font-weight:600;">{c.title}</span><br>
                            <span style="font-size:0.8rem; color:#6B7280;">📍 {c.ward.name if c.ward else 'City'} | {format_status_badge(c.status)}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(f"Track {c.complaint_number}", key=f"track_btn_{c.id}"):
                        st.session_state.search_complaint_num = c.complaint_number
                        st.rerun()

    # RENDER COMPLAINT DETAILS
    if complaint_to_display:
        c = complaint_to_display
        st.divider()

        # Header Badge Row
        h1, h2, h3, h4 = st.columns([2, 1, 1, 1])
        with h1:
            st.markdown(f"### {c.complaint_number}")
            st.caption(f"Filed on {format_datetime(c.created_at)}")
        with h2:
            st.markdown(f"**Status:**\n\n{format_status_badge(c.status)}")
        with h3:
            st.markdown(f"**Severity:**\n\n{format_severity_badge(c.severity)}")
        with h4:
            sla_info = sla_service.check_sla_status(c)
            st.markdown(f"**SLA Target:**\n\n{sla_info['badge']}")

        st.write("")

        # Progress Stepper
        status_order = ["SUBMITTED", "ACKNOWLEDGED", "ASSIGNED", "IN_PROGRESS", "RESOLVED"]
        current_idx = status_order.index(c.status) if c.status in status_order else 2

        prog_val = (current_idx + 1) / len(status_order)
        st.progress(prog_val, text=f"Current Stage: {format_status_badge(c.status)}")
        st.write("")

        # Two Column Layout: Details & Map vs Timeline
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown("#### 📄 **Grievance Details**")
            st.markdown(f"**Title:** {c.title}")
            st.markdown(f"**Description:** {c.description}")
            st.markdown(f"**Responsible Department:** {c.department.name if c.department else 'N/A'}")
            st.markdown(f"**Zonal Ward:** {c.ward.name if c.ward else 'Citywide'} ({c.ward.zone if c.ward else ''})")
            if c.assigned_officer:
                st.markdown(f"**Assigned Field Engineer:** {c.assigned_officer.designation} ({c.assigned_officer.employee_code})")

            # Location and Map
            if c.location:
                st.markdown("#### 📍 **Location**")
                st.write(f"**Address:** {c.location.address or 'N/A'}")
                if c.location.landmark:
                    st.write(f"**Landmark:** {c.location.landmark}")

                # Leaflet Map
                m_track = folium.Map(location=[c.location.latitude, c.location.longitude], zoom_start=15)
                folium.Marker(
                    [c.location.latitude, c.location.longitude],
                    popup=c.complaint_number,
                    tooltip=c.title,
                    icon=folium.Icon(color="blue", icon="info-sign"),
                ).add_to(m_track)
                st_folium(m_track, height=240, width=None, key="track_map")

            # Photos & Media
            if c.media:
                st.markdown("#### 📸 **Attached Media**")
                m_cols = st.columns(min(len(c.media), 3))
                for m_idx, med in enumerate(c.media):
                    file_path = storage.get_file_path(med.storage_path)
                    with m_cols[m_idx % 3]:
                        if file_path and os.path.exists(file_path) and med.media_type == "image":
                            try:
                                img = Image.open(file_path)
                                st.image(img, caption=med.original_filename, use_container_width=True)
                            except Exception:
                                st.caption(f"📁 {med.original_filename}")
                        else:
                            st.caption(f"🎥 {med.original_filename} ({med.media_type.upper()})")

        with col_right:
            st.markdown("#### ⏱️ **Lifecycle Timeline**")

            if c.status_history:
                for hist in c.status_history:
                    # Skip internal notes for regular citizens
                    if hist.is_internal_note:
                        continue

                    changed_by_name = hist.changed_by.full_name if hist.changed_by else "System"
                    st.markdown(
                        f"""
                        <div class="timeline-item">
                            <span style="font-weight:bold; color:#1E40AF;">{format_status_badge(hist.to_status)}</span>
                            <span style="font-size:0.78rem; color:#6B7280; float:right;">{format_datetime(hist.created_at)}</span><br>
                            <span style="font-size:0.88rem; color:#374151;">{hist.remarks or 'Status updated.'}</span><br>
                            <span style="font-size:0.75rem; color:#9CA3AF;">By: {changed_by_name}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No timeline logs recorded yet.")

            st.divider()

            # Citizen comment box
            st.markdown("#### 💬 **Add Clarification / Note**")
            new_comment = st.text_area("Post a message to the inspecting department", placeholder="e.g. The leak has worsened today...", height=80)
            if st.button("Post Message", type="secondary"):
                if not new_comment.strip():
                    st.error("Please enter a message.")
                else:
                    curr_u = get_current_user()
                    u_id = curr_u["user_id"] if curr_u else c.citizen_id
                    comp_service.add_comment(
                        complaint_id=c.id,
                        user_id=u_id,
                        comment_text=new_comment,
                        is_internal=False,
                    )
                    session.commit()
                    st.success("✅ Message posted successfully!")
                    st.rerun()

            # Display comment thread
            if c.comments:
                st.markdown("##### Previous Messages")
                for cm in c.comments:
                    if cm.is_internal:
                        continue
                    sender = cm.user.full_name if cm.user else "Citizen"
                    st.markdown(
                        f"""
                        <div style="background:#F1F5F9; border-radius:6px; padding:8px 12px; margin-bottom:6px; font-size:0.85rem;">
                            <b>{sender}</b> <span style="font-size:0.75rem; color:#64748B;">({format_datetime(cm.created_at)})</span><br>
                            {cm.comment}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
