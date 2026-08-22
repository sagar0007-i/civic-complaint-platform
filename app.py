"""CivicPulse - Production Civic Complaint Redressal Platform (Main Streamlit Entrypoint)."""

import os
import sys
from pathlib import Path
import streamlit as st

# Setup Path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config import settings
from backend.database import init_db, get_db_session
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

# Configure Page
st.set_page_config(
    page_title="CivicPulse - Civic Grievance & Municipal Resolution Platform",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database schema on startup
try:
    init_db()
except Exception as e:
    st.error(f"Database connection error: {e}")

# Initialize session state & styling
init_session_state()
apply_custom_css()

# Sidebar branding & authentication status
with st.sidebar:
    st.markdown(f"## {icon_svg('landmark', color='#1E3A8A', label='CivicPulse')} **CivicPulse**", unsafe_allow_html=True)
    st.caption("Citizen Grievance & Municipal Resolution Platform")
    st.divider()

    if is_logged_in():
        user = get_current_user()
        st.markdown(f"{icon_svg('user', size=18, color='#1E3A8A')} **{user.get('full_name')}**", unsafe_allow_html=True)
        st.markdown(f"Role: `{user.get('role')}`")
        if user.get("officer_profile"):
            dept_name = user["officer_profile"].get("department_name", "Department")
            desig = user["officer_profile"].get("designation", "Officer")
            st.caption(f"{dept_name}\n{desig}")

        if st.button("Log Out", use_container_width=True):
            logout_user()
            st.rerun()
    else:
        st.info("You are browsing as a **Guest**.")
        st.markdown("Log in or register to track grievances and receive notifications.")
        st.page_link("pages/10_Auth.py", label="Login / Register")

    st.divider()
    st.markdown(f"### {icon_svg('sparkles', color='#7C3AED')} **Evaluation Showcase**", unsafe_allow_html=True)
    st.page_link("pages/11_Evaluation_Dossier.py", label="Evaluation & Vision Dossier")
    st.page_link("pages/07_Analytics.py", label="Public Transparency Portal")

    st.divider()
    st.markdown(f"### {icon_svg('map-pin', color='#0F766E')} **Municipality**", unsafe_allow_html=True)
    st.caption(f"**City:** {settings.DEFAULT_CITY}\n**State:** {settings.DEFAULT_STATE}")

# -----------------------------------------------------------------------------
# HERO BANNER
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="hero-banner">
        <div class="hero-title">{icon_svg('landmark', size=32, color='#FFFFFF')} CivicPulse (NagarVani)</div>
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
        use_container_width=True,
    )
with cta_c2:
    st.page_link(
        "pages/03_Track_Complaint.py",
        label="Track Grievance Status",
        use_container_width=True,
    )
with cta_c3:
    st.page_link(
        "pages/11_Evaluation_Dossier.py",
        label="Evaluation & Tech Dossier",
        use_container_width=True,
    )
with cta_c4:
    st.page_link(
        "pages/07_Analytics.py",
        label="Public Transparency",
        use_container_width=True,
    )

st.write("")

# -----------------------------------------------------------------------------
# LIVE MUNICIPAL METRICS
# -----------------------------------------------------------------------------
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
st.markdown(f"### {icon_svg('lock', color='#1E3A8A')} **Access the Portal — Choose Your Role**", unsafe_allow_html=True)
st.caption("Each role has a dedicated, secure authentication flow. Click below to navigate to the Sign In page.")

r_c1, r_c2, r_c3, r_c4 = st.columns(4)

with r_c1:
    st.markdown(
        f"""
        <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;padding:1rem;text-align:center;">
            <div>{icon_svg('user', size=28, color='#2563EB')}</div>
            <strong style="color:#1A202C;">Citizen</strong>
            <p style="font-size:0.8rem;color:#475569;margin:0.4rem 0 0 0;">
                Register &amp; sign in to report civic issues in your ward.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r_c2:
    st.markdown(
        f"""
        <div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:10px;padding:1rem;text-align:center;">
            <div>{icon_svg('hard-hat', size=28, color='#16A34A')}</div>
            <strong style="color:#1A202C;">Field Officer</strong>
            <p style="font-size:0.8rem;color:#475569;margin:0.4rem 0 0 0;">
                Register with your Employee Code &amp; sign in to manage assigned grievances.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r_c3:
    st.markdown(
        f"""
        <div style="background:#FFF7ED;border:1px solid #FED7AA;border-radius:10px;padding:1rem;text-align:center;">
            <div>{icon_svg('building', size=28, color='#EA580C')}</div>
            <strong style="color:#1A202C;">Dept Admin</strong>
            <p style="font-size:0.8rem;color:#475569;margin:0.4rem 0 0 0;">
                Requires credentials + confidential <strong>Dept Admin Access Code</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r_c4:
    st.markdown(
        f"""
        <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;padding:1rem;text-align:center;">
            <div>{icon_svg('shield-check', size=28, color='#DC2626')}</div>
            <strong style="color:#1A202C;">Super Admin</strong>
            <p style="font-size:0.8rem;color:#475569;margin:0.4rem 0 0 0;">
                Requires credentials + <strong>Commissioner's Authorisation Code</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
if st.button("Go to Secure Sign In / Register Page", type="primary", use_container_width=False):
    st.switch_page("pages/10_Auth.py")

st.divider()

# -----------------------------------------------------------------------------
# HOW CIVICPULSE WORKS
# -----------------------------------------------------------------------------
st.markdown(f"### {icon_svg('route', color='#1E3A8A')} **End-to-End Resolution Workflow**", unsafe_allow_html=True)
w1, w2, w3, w4 = st.columns(4)

with w1:
    st.markdown(
        f"""
        <div class="eval-card" style="border-top: 4px solid #3B82F6;">
            <h4 style="color:#1E3A8A; margin-top:0;">{icon_svg('camera', color='#1E3A8A')} 1. Fast Report</h4>
            <p style="font-size:0.88rem; color:#475569;">Upload photos/video, pin GPS map coordinates, and describe the issue in under 2 minutes.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with w2:
    st.markdown(
        f"""
        <div class="eval-card" style="border-top: 4px solid #6366F1;">
            <h4 style="color:#1E3A8A; margin-top:0;">{icon_svg('route', color='#1E3A8A')} 2. Auto Routing</h4>
            <p style="font-size:0.88rem; color:#475569;">Database routing engine matches category + ward + city to immediately dispatch to the local zonal team.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with w3:
    st.markdown(
        f"""
        <div class="eval-card" style="border-top: 4px solid #F59E0B;">
            <h4 style="color:#1E3A8A; margin-top:0;">{icon_svg('hard-hat', color='#1E3A8A')} 3. Field Action</h4>
            <p style="font-size:0.88rem; color:#475569;">Authorized municipal engineers inspect the site, triage with AI summaries, and dispatch repair equipment.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with w4:
    st.markdown(
        f"""
        <div class="eval-card" style="border-top: 4px solid #10B981;">
            <h4 style="color:#1E3A8A; margin-top:0;">{icon_svg('circle-check', color='#1E3A8A')} 4. Verified Fix</h4>
            <p style="font-size:0.88rem; color:#475569;">Field engineer submits resolution proof photo, closes the SLA ticket, and notifies citizen in real time.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# -----------------------------------------------------------------------------
# CATEGORIES SHOWCASE
# -----------------------------------------------------------------------------
st.markdown(f"### {icon_svg('layers', color='#1E3A8A')} **Civic Problems Handled**", unsafe_allow_html=True)
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
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:10px; margin-bottom:10px;">
                    {category_icon(c.slug)} <b style="color:#0F172A;">{c.name}</b><br>
                    <span style="font-size:0.8rem; color:#1E293B;">Default SLA Priority: <b style="color:#0F172A;">{c.default_severity}</b></span>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.divider()

# -----------------------------------------------------------------------------
# RECENTLY RESOLVED PUBLIC SHOWCASE
# -----------------------------------------------------------------------------
if showcase:
    st.markdown(f"### {icon_svg('circle-check', color='#15803D')} **Recently Resolved by Municipal Authorities**", unsafe_allow_html=True)
    res_cols = st.columns(len(showcase))
    for idx, item in enumerate(showcase):
        with res_cols[idx]:
            st.markdown(
                f"""
                <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:12px;">
                    <span style="font-size:0.8rem; font-weight:bold; color:#15803D;">{item['complaint_number']}</span>
                    <h5 style="margin:4px 0; color:#166534;">{icon_svg('tag', size=18, color='#15803D')} {item['title']}</h5>
                    <p style="font-size:0.85rem; color:#374151; margin-bottom:4px;">{icon_svg('map-pin', size=16, color='#475569')} {item['ward']}</p>
                    <span style="font-size:0.75rem; color:#15803D; font-weight:600;">{icon_svg('circle-check', size=16, color='#15803D')} Resolved</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.write("")
st.caption("CivicPulse (NagarVani) - Municipal Grievance Redressal Platform | Internal Evaluation Edition 2026")
