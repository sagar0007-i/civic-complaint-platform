"""CivicPulse — Main Navigation Entry Point (Streamlit Multi-Page App)."""

import sys
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.database import init_db
from backend.utils.session import (
    init_session_state,
    get_current_user,
    is_logged_in,
    logout_user,
    apply_custom_css,
)
from backend.config import settings
from backend.utils.icons import icon_svg

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="CivicPulse — Mumbai BMC Grievance Portal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Initialize DB on cold start ───────────────────────────────────────────────
try:
    init_db()
except Exception as e:
    st.error(f"Database connection error: {e}")

# ── Navigation with CAPITAL sidebar labels ────────────────────────────────────
pages = st.navigation(
    {
        "CIVICPULSE": [
            st.Page("pages/01_Home.py",              title="HOME"),
        ],
        "CITIZEN": [
            st.Page("pages/02_Report_Problem.py",    title="REPORT PROBLEM"),
            st.Page("pages/03_Track_Complaint.py",   title="TRACK COMPLAINT"),
            st.Page("pages/04_My_Complaints.py",     title="MY COMPLAINTS"),
        ],
        "OFFICER & ADMIN": [
            st.Page("pages/05_Officer_Dashboard.py", title="OFFICER DASHBOARD"),
            st.Page("pages/06_Admin_Dashboard.py",   title="ADMIN DASHBOARD"),
        ],
        "PUBLIC": [
            st.Page("pages/07_Analytics.py",         title="ANALYTICS"),
            st.Page("pages/11_Evaluation_Dossier.py",title="EVALUATION DOSSIER"),
        ],
        "ACCOUNT": [
            st.Page("pages/08_Notifications.py",     title="NOTIFICATIONS"),
            st.Page("pages/09_Profile.py",           title="PROFILE"),
            st.Page("pages/10_Auth.py",              title="LOGIN / REGISTER"),
        ],
    }
)

# ── Global Sidebar: Branding + Auth Status ────────────────────────────────────
init_session_state()
apply_custom_css()

with st.sidebar:
    st.divider()
    st.markdown(
        """
        <div style="text-align:center; padding: 0.5rem 0 0.8rem;">
            <div style="font-size:2.2rem;">🏛️</div>
            <div style="font-family:'Rajdhani',sans-serif; font-size:1.5rem; font-weight:700;
                        color:#ffffff; letter-spacing:0.08em;">CivicPulse</div>
            <div style="font-size:0.72rem; color:rgba(199,212,240,0.75);
                        letter-spacing:0.06em; margin-top:2px;">NAGARVANI · MUMBAI BMC</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    if is_logged_in():
        user = get_current_user()
        role_colors = {"CITIZEN": "#10b981", "OFFICER": "#f59e0b", "DEPT_ADMIN": "#ff9900", "SUPER_ADMIN": "#ef4444"}
        role = user.get("role", "")
        role_color = role_colors.get(role, "#c7d4f0")
        st.markdown(
            f"""
            <div style="background:rgba(255,255,255,0.07); border-radius:10px;
                        padding:0.75rem 1rem; margin-bottom:0.5rem;
                        border:1px solid rgba(255,255,255,0.12);">
                <div style="font-weight:700; color:#ffffff; font-size:0.95rem;">
                    👤 {user.get('full_name')}
                </div>
                <div style="font-size:0.75rem; margin-top:3px;">
                    <span style="background:{role_color}22; color:{role_color};
                                 border:1px solid {role_color}44; border-radius:4px;
                                 padding:1px 8px; font-weight:700; font-size:0.72rem;
                                 letter-spacing:0.05em;">
                        {role}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if user.get("officer_profile"):
            dept = user["officer_profile"].get("department_name", "")
            desig = user["officer_profile"].get("designation", "")
            st.caption(f"🏢 {dept} · {desig}")
        if st.button("🚪 Log Out", width="stretch"):
            logout_user()
            st.rerun()
    else:
        st.markdown(
            """
            <div style="background:rgba(255,255,255,0.05); border-radius:10px;
                        padding:0.75rem 1rem; border:1px solid rgba(255,255,255,0.1);
                        text-align:center; margin-bottom:0.5rem;">
                <div style="color:rgba(199,212,240,0.8); font-size:0.85rem;">
                    👋 Browsing as <strong style="color:#fff;">Guest</strong>
                </div>
                <div style="color:rgba(199,212,240,0.6); font-size:0.75rem; margin-top:4px;">
                    Sign in to file & track grievances
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Run the selected page ─────────────────────────────────────────────────────
pages.run()
