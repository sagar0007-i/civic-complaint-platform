"""Citizen Grievance Dashboard - My Complaints."""

import os
import sys
from pathlib import Path
import streamlit as st

# Setup Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.database import get_db_session
from backend.services.complaint_service import ComplaintService
from backend.services.sla_service import SLAService
from backend.utils.formatting import format_status_badge, format_severity_badge, format_datetime
from backend.utils.session import init_session_state, get_current_user, is_logged_in, apply_custom_css
from backend.utils.icons import icon_svg

init_session_state()
apply_custom_css()

st.markdown(f'<h1 class="main-header">{icon_svg("file-text", size=28, color="#1E3A8A")} My Complaints</h1>', unsafe_allow_html=True)

if not is_logged_in():
    st.info("🔒 Please log in with your citizen account to view and manage your filed complaints.")
    st.page_link("pages/10_Auth.py", label="🔐 Go to Login / Register", icon="👉")
    st.stop()

user = get_current_user()
st.caption(f"Logged in as **{user['full_name']}** (`{user['email']}`)")

with get_db_session() as session:
    comp_service = ComplaintService(session)
    sla_service = SLAService(session)

    # Fetch user's complaints
    user_complaints = comp_service.list_complaints(citizen_id=user["user_id"], limit=100)

    # Metric summaries
    total = len(user_complaints)
    resolved = sum(1 for c in user_complaints if c.status == "RESOLVED")
    in_progress = sum(1 for c in user_complaints if c.status in ["ACKNOWLEDGED", "ASSIGNED", "IN_PROGRESS", "SUBMITTED"])

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Filed", total)
    m2.metric("Active / In Progress", in_progress, delta="Pending Resolution")
    m3.metric("Resolved", resolved, delta=f"{(resolved/total*100):.0f}%" if total > 0 else "0%")

    st.divider()

    # Filter Bar
    filter_col1, filter_col2 = st.columns([2, 2])
    with filter_col1:
        status_filter = st.selectbox(
            "Filter by Status",
            options=["ALL", "SUBMITTED", "IN_PROGRESS", "RESOLVED", "WAITING_FOR_INFORMATION", "REJECTED"],
        )
    with filter_col2:
        search_kw = st.text_input("Search my complaints", placeholder="e.g. street, pothole, garbage")

    filtered = user_complaints
    if status_filter != "ALL":
        filtered = [c for c in filtered if c.status == status_filter]
    if search_kw:
        kw = search_kw.lower()
        filtered = [c for c in filtered if kw in c.title.lower() or kw in c.complaint_number.lower() or kw in c.description.lower()]

    if not filtered:
        st.info("No complaints found matching current filters.")
        if st.button("📢 File a New Complaint"):
            st.switch_page("pages/02_Report_Problem.py")
    else:
        for c in filtered:
            sla_info = sla_service.check_sla_status(c)
            with st.expander(f"**{c.complaint_number}** - {c.title} ({format_status_badge(c.status)})"):
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.write(f"**Description:** {c.description}")
                    st.write(f"📍 **Location:** {c.location.address if c.location else settings.DEFAULT_CITY}")
                    if c.landmark:
                        st.write(f"📌 **Landmark:** {c.landmark}")
                with c2:
                    st.write(f"🏢 **Department:** {c.department.name if c.department else 'N/A'}")
                    st.write(f"🏷️ **Category:** {c.category.name if c.category else 'N/A'}")
                    st.write(f"⚡ **Severity:** {format_severity_badge(c.severity)}")
                with c3:
                    st.write(f"📅 **Date Filed:** {format_datetime(c.created_at)}")
                    st.write(f"⏱️ **SLA Status:** {sla_info['badge']}")
                    if st.button("🔍 View Full Timeline & Map", key=f"btn_my_{c.id}", use_container_width=True):
                        st.session_state.search_complaint_num = c.complaint_number
                        st.switch_page("pages/03_Track_Complaint.py")

                if c.delay_reason:
                    revised_str = format_datetime(c.revised_resolution_target) if c.revised_resolution_target else "Accelerated"
                    st.markdown(
                        f"""
                        <div style="background:#fffbeb; border:1px solid #f59e0b; border-radius:8px; padding:10px 14px; margin-top:8px; font-size:0.85rem;">
                            <b style="color:#b45309;">🏛️ Official Department Delay Justification:</b> "{c.delay_reason}"<br>
                            <span style="color:#78350f; font-size:0.78rem;">Accountable Officer: {c.delay_justified_by or 'BMC Official'} | Revised Target: <b>{revised_str}</b></span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

