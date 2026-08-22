"""CivicPulse Home Page."""

import os
import sys
from pathlib import Path
import streamlit as st

# Setup Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config import settings
from backend.database import get_db_session
from backend.utils.session import init_session_state, apply_custom_css
from backend.utils.icons import icon_svg
from backend.services.analytics_service import AnalyticsService

init_session_state()
apply_custom_css()

# Header
st.markdown(
    f"""
    <div class="hero-banner">
        <div class="hero-title">{icon_svg('landmark', size=32, color='#FFFFFF')} Civic Grievance Redressal Portal</div>
        <div class="hero-subtitle">
            Direct civic problem reporting with transparent tracking, automated department routing, and verified field resolutions.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Navigation Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.page_link("pages/02_Report_Problem.py", label="Report a Problem", use_container_width=True)
with c2:
    st.page_link("pages/03_Track_Complaint.py", label="Track Complaint", use_container_width=True)
with c3:
    st.page_link("pages/11_Evaluation_Dossier.py", label="Evaluation Dossier", use_container_width=True)
with c4:
    st.page_link("pages/07_Analytics.py", label="Transparency Portal", use_container_width=True)

st.divider()

# Public Stats
try:
    with get_db_session() as session:
        analytics = AnalyticsService(session)
        kpis = analytics.get_summary_kpis()
        showcase = analytics.get_public_resolved_showcase(limit=4)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Grievances", f"{kpis['total']:,}")
    m2.metric("In Progress", f"{kpis['in_progress']:,}", delta="Active")
    m3.metric("Resolved", f"{kpis['resolved']:,}", f"{kpis['resolution_rate']}% Rate")
    m4.metric("Average Turnaround", f"{kpis['avg_resolution_hours']} hrs")
    m5.metric("Escalations", f"{kpis['escalated']:,}", delta_color="inverse")

    if showcase:
        st.write("")
        st.markdown("### 🌟 **Recently Resolved Cases**")
        res_cols = st.columns(len(showcase))
        for idx, item in enumerate(showcase):
            with res_cols[idx]:
                st.markdown(
                    f"""
                    <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:12px;">
                        <span style="font-size:0.8rem; font-weight:bold; color:#15803D;">{item['complaint_number']}</span>
                        <h5 style="margin:4px 0; color:#166534;">{item['category_icon']} {item['title']}</h5>
                        <p style="font-size:0.85rem; color:#374151;">📍 {item['ward']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
except Exception as e:
    st.info("Loading civic statistics...")
