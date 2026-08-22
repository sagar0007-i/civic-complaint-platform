"""In-App Notifications Center."""

import os
import sys
from pathlib import Path
import streamlit as st

# Setup Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.database import get_db_session
from backend.services.notification_service import NotificationService
from backend.utils.formatting import format_datetime
from backend.utils.session import init_session_state, get_current_user, is_logged_in, apply_custom_css
from backend.utils.icons import icon_svg

init_session_state()
apply_custom_css()

st.markdown(f'<h1 class="main-header">{icon_svg("circle-check", size=28, color="#1E3A8A")} Notification Center</h1>', unsafe_allow_html=True)

if not is_logged_in():
    st.info("Please log in to view your complaint alerts and status notifications.")
    st.page_link("pages/10_Auth.py", label="Login / Register")
    st.stop()

user = get_current_user()

with get_db_session() as session:
    notif_service = NotificationService(session)
    notifications = notif_service.get_user_notifications(user["user_id"])

    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        st.caption(f"Notifications for **{user['full_name']}**")
    with top_col2:
        if notifications and st.button("Mark All as Read"):
            notif_service.mark_all_read(user["user_id"])
            st.success("All marked as read!")
            st.rerun()

    if not notifications:
        st.info("You have no notifications at this time.")
    else:
        for n in notifications:
            bg_color = "#FFFFFF" if n.is_read else "#EFF6FF"
            border_color = "#E2E8F0" if n.is_read else "#3B82F6"
            badge = "Read" if n.is_read else "**NEW**"

            with st.container():
                st.markdown(
                    f"""
                    <div style="background:{bg_color}; border-left:4px solid {border_color}; border-radius:6px; padding:12px; margin-bottom:10px; box-shadow:0 1px 2px rgba(0,0,0,0.04);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:bold; font-size:0.95rem; color:#1E3A8A;">{n.title}</span>
                            <span style="font-size:0.75rem; color:#6B7280;">{format_datetime(n.created_at)} | {badge}</span>
                        </div>
                        <p style="margin:6px 0 0 0; font-size:0.88rem; color:#374151;">{n.message}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if not n.is_read:
                    if st.button("Mark Read", key=f"rd_{n.id}", type="secondary"):
                        notif_service.mark_as_read(n.id)
                        st.rerun()
