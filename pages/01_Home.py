"""CivicPulse — Home Page."""

import sys
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config import settings
from backend.database import get_db_session
from backend.utils.session import (
    init_session_state,
    get_current_user,
    is_logged_in,
    get_current_role,
    logout_user,
    apply_custom_css,
)
from backend.services.analytics_service import AnalyticsService
from backend.repositories.category_repo import CategoryRepository
from backend.utils.icons import category_icon, icon_svg

init_session_state()
apply_custom_css()

# -----------------------------------------------------------------------------
# HERO BANNER
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="hero-banner">
        <div class="hero-title">{icon_svg('landmark', size=32, color='#FFFFFF')} HOME — CivicPulse (NagarVani)</div>
        <div class="hero-subtitle">
            Next-generation civic problem reporting, automated geospatial routing, and municipal field resolution platform. Empowering citizens and urban local bodies with radical transparency.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Quick Action Hub
cta_c1, cta_c2, cta_c3, cta_c4 = st.columns(4)
with cta_c1:
    st.page_link(
        "pages/02_Report_Problem.py",
        label="File Complaint (2 Min)",
        icon=":material/description:",
        width="stretch",
    )
with cta_c2:
    st.page_link(
        "pages/03_Track_Complaint.py",
        label="Track Grievance Status",
        icon=":material/search:",
        width="stretch",
    )
with cta_c3:
    st.page_link(
        "pages/11_Evaluation_Dossier.py",
        label="Evaluation & Tech Dossier",
        icon=":material/code:",
        width="stretch",
    )
with cta_c4:
    st.page_link(
        "pages/07_Analytics.py",
        label="Public Transparency",
        icon=":material/visibility:",
        width="stretch",
    )

st.write("")

# -----------------------------------------------------------------------------
# LIVE MUNICIPAL METRICS
# -----------------------------------------------------------------------------
st.markdown("### LIVE MUNICIPAL METRICS")
showcase = []
try:
    with get_db_session() as session:
        analytics = AnalyticsService(session)
        kpis = analytics.get_summary_kpis()
        showcase = analytics.get_public_resolved_showcase(limit=4)

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric(label="Total Grievances", value=f"{kpis['total']:,}")
    with m2:
        st.metric(label="In Progress", value=f"{kpis['in_progress']:,}", delta="Active")
    with m3:
        st.metric(label="Resolved Issues", value=f"{kpis['resolved']:,}", delta=f"{kpis['resolution_rate']}% Rate")
    with m4:
        st.metric(label="Avg Resolution", value=f"{kpis['avg_resolution_hours']} hrs")
    with m5:
        st.metric(label="Escalations", value=f"{kpis['escalated']:,}", delta_color="inverse")
except Exception as e:
    st.warning(f"Loading municipal statistics: {e}")

st.divider()

# -----------------------------------------------------------------------------
# ACCESS PORTAL GUIDE
# -----------------------------------------------------------------------------
st.markdown("### ACCESS THE PORTAL — CHOOSE YOUR ROLE")
st.caption("Each role has a dedicated, secure sign-in flow.")

r_c1, r_c2, r_c3, r_c4 = st.columns(4)

with r_c1:
    st.markdown(
        """
        <div class="role-card" style="text-align:center; border-top: 4px solid #1a4a9e;">
            <div style="font-size:2rem; margin-bottom:6px;">🏘️</div>
            <strong style="color:#0f2d6b; font-size:1rem; display:block; margin-bottom:6px;">CITIZEN</strong>
            <p style="font-size:0.82rem; color:#64748b; margin:0;">
                Register &amp; sign in to report civic issues in your ward.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r_c2:
    st.markdown(
        """
        <div class="role-card" style="text-align:center; border-top: 4px solid #059669;">
            <div style="font-size:2rem; margin-bottom:6px;">🔧</div>
            <strong style="color:#0f2d6b; font-size:1rem; display:block; margin-bottom:6px;">FIELD OFFICER</strong>
            <p style="font-size:0.82rem; color:#64748b; margin:0;">
                Register with Employee Code &amp; sign in to manage tasks.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r_c3:
    st.markdown(
        """
        <div class="role-card" style="text-align:center; border-top: 4px solid #d97706;">
            <div style="font-size:2rem; margin-bottom:6px;">🏢</div>
            <strong style="color:#0f2d6b; font-size:1rem; display:block; margin-bottom:6px;">DEPT ADMIN</strong>
            <p style="font-size:0.82rem; color:#64748b; margin:0;">
                Credentials + confidential Dept Admin Access Code.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r_c4:
    st.markdown(
        """
        <div class="role-card" style="text-align:center; border-top: 4px solid #dc2626;">
            <div style="font-size:2rem; margin-bottom:6px;">🎖️</div>
            <strong style="color:#0f2d6b; font-size:1rem; display:block; margin-bottom:6px;">SUPER ADMIN</strong>
            <p style="font-size:0.82rem; color:#64748b; margin:0;">
                Commissioner's Authorisation Code required.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
if st.button("Go to Sign In / Register", icon=":material/login:", type="primary", width="content"):
    st.switch_page("pages/10_Auth.py")

st.divider()

# -----------------------------------------------------------------------------
# HOW CIVICPULSE WORKS
# -----------------------------------------------------------------------------
st.markdown("### HOW IT WORKS — END TO END")
w1, w2, w3, w4 = st.columns(4)

with w1:
    st.markdown(
        """
        <div style="background:#fff; border:1.5px solid #e2e8f0; border-radius:12px;
                    padding:1.25rem; border-left:5px solid #1a4a9e; height:100%;
                    box-shadow:0 2px 8px rgba(15,45,107,0.07);">
            <div style="font-size:1.6rem; margin-bottom:6px;">📸</div>
            <h4 style="color:#0f2d6b; margin:0 0 6px; font-size:1rem;">1. REPORT</h4>
            <p style="font-size:0.86rem; color:#64748b; margin:0; line-height:1.6;">
                Upload photos, pin the location on map, and describe the problem in under 2 minutes.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with w2:
    st.markdown(
        """
        <div style="background:#fff; border:1.5px solid #e2e8f0; border-radius:12px;
                    padding:1.25rem; border-left:5px solid #d97706; height:100%;
                    box-shadow:0 2px 8px rgba(15,45,107,0.07);">
            <div style="font-size:1.6rem; margin-bottom:6px;">🗺️</div>
            <h4 style="color:#0f2d6b; margin:0 0 6px; font-size:1rem;">2. AUTO-ROUTE</h4>
            <p style="font-size:0.86rem; color:#64748b; margin:0; line-height:1.6;">
                System auto-assigns to the correct ward & department based on category and GPS pin.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with w3:
    st.markdown(
        """
        <div style="background:#fff; border:1.5px solid #e2e8f0; border-radius:12px;
                    padding:1.25rem; border-left:5px solid #ea580c; height:100%;
                    box-shadow:0 2px 8px rgba(15,45,107,0.07);">
            <div style="font-size:1.6rem; margin-bottom:6px;">👷</div>
            <h4 style="color:#0f2d6b; margin:0 0 6px; font-size:1rem;">3. FIELD ACTION</h4>
            <p style="font-size:0.86rem; color:#64748b; margin:0; line-height:1.6;">
                Field engineer visits site, reviews AI triage summary, and dispatches repair crew.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with w4:
    st.markdown(
        """
        <div style="background:#fff; border:1.5px solid #e2e8f0; border-radius:12px;
                    padding:1.25rem; border-left:5px solid #059669; height:100%;
                    box-shadow:0 2px 8px rgba(15,45,107,0.07);">
            <div style="font-size:1.6rem; margin-bottom:6px;">✅</div>
            <h4 style="color:#0f2d6b; margin:0 0 6px; font-size:1rem;">4. RESOLVED</h4>
            <p style="font-size:0.86rem; color:#64748b; margin:0; line-height:1.6;">
                Engineer uploads proof photo, closes ticket, citizen is notified instantly.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# -----------------------------------------------------------------------------
# CATEGORIES SHOWCASE
# -----------------------------------------------------------------------------
st.markdown("### CIVIC PROBLEMS WE HANDLE")
with get_db_session() as session:
    cat_repo = CategoryRepository(session)
    categories = cat_repo.get_all(active_only=True)

if categories:
    cat_cols = st.columns(4)
    for idx, c in enumerate(categories):
        col = cat_cols[idx % 4]
        with col:
            st.markdown(
                f"""
                <div style="background:#ffffff; border:1.5px solid #e2e8f0; border-radius:10px;
                            padding:12px; margin-bottom:10px;
                            box-shadow:0 2px 6px rgba(15,45,107,0.06);">
                    {category_icon(c.slug)} <b style="color:#0f2d6b;">{c.name}</b><br>
                    <span style="font-size:0.78rem; color:#64748b;">
                        SLA Priority: <b style="color:#ff9900;">{c.default_severity}</b>
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.divider()

# -----------------------------------------------------------------------------
# RECENTLY RESOLVED PUBLIC SHOWCASE
# -----------------------------------------------------------------------------
if showcase:
    st.markdown("### RECENTLY RESOLVED BY BMC MUMBAI")
    res_cols = st.columns(len(showcase))
    for idx, item in enumerate(showcase):
        with res_cols[idx]:
            st.markdown(
                f"""
                <div style="background:#ffffff; border:1.5px solid #e2e8f0;
                            border-left:5px solid #059669; border-radius:10px;
                            padding:14px; box-shadow:0 2px 8px rgba(15,45,107,0.07);">
                    <div style="font-size:0.75rem; font-weight:700; color:#059669;
                                letter-spacing:0.05em; margin-bottom:4px;">
                        ✔ {item['complaint_number']}
                    </div>
                    <div style="font-weight:700; color:#0f2d6b; font-size:0.9rem;
                                margin-bottom:4px;">{item['title']}</div>
                    <div style="font-size:0.8rem; color:#64748b;">
                        📍 {item['ward']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.write("")
st.caption("CivicPulse (NagarVani) · Municipal Grievance Redressal Platform · Mumbai BMC · Evaluation Edition 2026")
