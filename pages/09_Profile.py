"""Citizen & Officer Profile Management."""

import os
import sys
from pathlib import Path
import streamlit as st

# Setup Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.database import get_db_session
from backend.repositories.user_repo import UserRepository
from backend.utils.formatting import format_datetime
from backend.utils.session import init_session_state, get_current_user, is_logged_in, logout_user, apply_custom_css

init_session_state()
apply_custom_css()

st.markdown('<h1 class="main-header">👤 User Profile</h1>', unsafe_allow_html=True)

if not is_logged_in():
    st.info("🔒 Please log in to view and manage your profile.")
    st.page_link("pages/10_Auth.py", label="🔐 Login / Register", icon="👉")
    st.stop()

user_sess = get_current_user()

with get_db_session() as session:
    user_repo = UserRepository(session)
    user_db = user_repo.get_by_id(user_sess["user_id"])

    if not user_db:
        st.error("User record not found.")
        st.stop()

    st.markdown(
        f"""
        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:20px; margin-bottom:20px;">
            <h3>{user_db.full_name}</h3>
            <p style="color:#64748B; margin-bottom:8px;">📧 {user_db.email} | 📞 {user_db.phone or 'No phone registered'}</p>
            <span style="background:#DBEAFE; color:#1E40AF; padding:4px 10px; border-radius:6px; font-weight:bold; font-size:0.85rem;">Role: {user_db.role}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if user_db.officer_profile:
        off = user_db.officer_profile
        st.markdown("#### 🏢 **Government Officer Profile**")
        st.write(f"**Department:** {off.department.name if off.department else 'N/A'}")
        st.write(f"**Designation:** {off.designation}")
        st.write(f"**Employee Code:** `{off.employee_code}`")
        if off.ward:
            st.write(f"**Assigned Ward:** {off.ward.name} ({off.ward.zone})")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"📅 **Member Since:** {format_datetime(user_db.created_at)}")
    with col2:
        if st.button("🚪 Log Out", type="secondary"):
            logout_user()
            st.success("Logged out.")
            st.rerun()
