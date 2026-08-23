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

st.markdown(
    f'<h1 class="main-header">{icon_svg("circle-check", size=28, color="#0F2D6B")} Notification Center</h1>',
    unsafe_allow_html=True,
)

if not is_logged_in():
    st.info("🔒 Please log in to view your grievance alerts and status notifications.")
    st.page_link("pages/10_Auth.py", label="Login / Register", width="stretch")
    st.stop()

user = get_current_user()

with get_db_session() as session:
    notif_service = NotificationService(session)
    notifications = notif_service.get_user_notifications(user["user_id"])
    unread_count = sum(1 for n in notifications if not n.is_read)

    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        if unread_count > 0:
            st.markdown(f"Notifications for **{user['full_name']}** · <span style='color:#059669; font-weight:700;'>({unread_count} Unread)</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"Notifications for **{user['full_name']}** · <span style='color:#64748B; font-weight:600;'>(All caught up)</span>", unsafe_allow_html=True)

    with top_col2:
        if unread_count > 0:
            if st.button("Mark All as Read", key="mark_all_btn", type="secondary", width="stretch"):
                notif_service.mark_all_read(user["user_id"])
                session.commit()
                st.session_state["notif_msg"] = "✅ All notifications marked as read."
                st.rerun()

    if "notif_msg" in st.session_state:
        st.success(st.session_state.pop("notif_msg"))

    if not notifications:
        st.info("🔔 You have no notifications at this time.")
    else:
        for n in notifications:
            # High-contrast styling for unread vs read notifications
            if n.is_read:
                bg_color = "#F8FAFC"
                border_color = "#CBD5E1"
                title_color = "#334155"
                msg_color = "#475569"
                badge_html = '<span style="background:#F1F5F9; color:#64748B; font-weight:600; border:1px solid #E2E8F0; border-radius:4px; padding:2px 8px; font-size:0.72rem;">READ</span>'
            else:
                bg_color = "#FFFFFF"
                border_color = "#2563EB"
                title_color = "#0F2D6B"
                msg_color = "#1E293B"
                badge_html = '<span style="background:#EFF6FF; color:#1D4ED8; font-weight:700; border:1px solid #BFDBFE; border-radius:4px; padding:2px 8px; font-size:0.72rem;">NEW</span>'

            col_card, col_action = st.columns([5, 1])
            with col_card:
                st.markdown(
                    f"""
                    <div style="background:{bg_color}; border-left:4px solid {border_color}; border-radius:8px; padding:14px 16px; margin-bottom:10px; box-shadow:0 2px 6px rgba(15,45,107,0.06); border-top:1px solid #E2E8F0; border-right:1px solid #E2E8F0; border-bottom:1px solid #E2E8F0;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:700; font-size:0.98rem; color:{title_color};">{n.title}</span>
                            <span style="font-size:0.78rem; color:#64748B; display:flex; align-items:center; gap:8px;">
                                {format_datetime(n.created_at)} · {badge_html}
                            </span>
                        </div>
                        <p style="margin:8px 0 0 0; font-size:0.9rem; color:{msg_color}; line-height:1.5;">{n.message}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_action:
                if not n.is_read:
                    if st.button("Mark Read", key=f"rd_{n.id}", type="secondary", width="stretch"):
                        notif_service.mark_as_read(n.id)
                        session.commit()
                        st.rerun()

