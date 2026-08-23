"""CivicPulse - Live Interactive Algorithm & Technology Demonstration Hub."""

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
from backend.services.ai_service import AIService, HeuristicAIProvider
from backend.services.routing_service import RoutingService
from backend.services.sla_service import SLAService
from backend.repositories.category_repo import CategoryRepository
from backend.repositories.ward_repo import WardRepository
from backend.repositories.department_repo import DepartmentRepository
from backend.utils.session import init_session_state, apply_custom_css
from backend.utils.icons import icon_svg

init_session_state()
apply_custom_css()

# Header Banner
st.markdown(
    f"""
    <div class="hero-banner">
        <div class="hero-title">{icon_svg('cpu', size=32, color='#FFFFFF')} Live Interactive Technology Demonstration Hub</div>
        <div class="hero-subtitle">
            Live sandbox to test and evaluate the core underlying algorithms of <b>CivicPulse Mumbai</b> in real-time.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Simulation Selector
demo_choice = st.radio(
    "Select Interactive Simulation Engine:",
    options=[
        "🤖 AI Classifier & Briefing Sandbox",
        "🔀 Dynamic Routing Rules Simulator",
        "⏱️ SLA Deadline & Risk Calculator",
    ],
    horizontal=True,
)

st.divider()

# -----------------------------------------------------------------------------
# 1. AI Classifier Sandbox
# -----------------------------------------------------------------------------
if demo_choice == "🤖 AI Classifier & Briefing Sandbox":
    st.markdown("### 🤖 **Deterministic AI NLP Co-Pilot Sandbox**")
    st.caption("Type any real-world civic complaint text to observe automatic category classification, severity estimation, and officer briefing generation:")

    test_title = st.text_input("Sample Complaint Title", value="Water pipeline leaking heavily on main road")
    test_desc = st.text_area(
        "Sample Citizen Description",
        value="Clean drinking water is bursting out of the underground pipe joint near the signal. Thousands of liters being wasted.",
        height=100,
    )
    test_landmark = st.text_input("Landmark", value="Opposite Metro Station")

    if st.button("🚀 Run NLP Inference & Analysis", type="primary", use_container_width=True):
        ai_svc = AIService(provider=HeuristicAIProvider())
        bundle = ai_svc.get_suggestions(test_title, test_desc, test_landmark)

        res1, res2, res3 = st.columns(3)
        with res1:
            st.metric("Suggested Category", bundle["suggested_category_slug"].upper())
        with res2:
            st.metric("Estimated Severity", bundle["suggested_severity"])
        with res3:
            st.metric("NLP Confidence", f"{(bundle['confidence_score']*100):.0f}%")

        st.markdown(
            f"""
            <div style="background:#EFF6FF; border:1.5px solid #BFDBFE; border-radius:10px; padding:16px; margin-top:14px;">
                <span style="font-weight:bold; color:#1E40AF; font-size:1.05rem;">🤖 Generated Officer Field Summary:</span><br>
                <p style="color:#1E3A8A; font-size:0.95rem; margin-top:6px; line-height:1.5;">{bundle['summary_text']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# -----------------------------------------------------------------------------
# 2. Dynamic Routing Matrix Simulator
# -----------------------------------------------------------------------------
elif demo_choice == "🔀 Dynamic Routing Rules Simulator":
    st.markdown("### 🔀 **Dynamic Database Routing Matrix Simulator**")
    st.caption("Simulate complaint routing to observe how database rules dynamically resolve the responsible department and engineer:")

    with get_db_session() as session:
        cat_repo = CategoryRepository(session)
        ward_repo = WardRepository(session)
        routing_svc = RoutingService(session)

        cats = cat_repo.get_all(active_only=True)
        wards = ward_repo.get_all(active_only=True)

        cat_map = {f"{c.icon} {c.name}": c.id for c in cats}
        ward_map = {f"{w.name} ({w.zone})": w.id for w in wards}

        r_col1, r_col2 = st.columns(2)
        with r_col1:
            sel_cat_label = st.selectbox("Select Complaint Category", list(cat_map.keys()))
        with r_col2:
            sel_ward_label = st.selectbox("Select Ward Location", list(ward_map.keys()))

        if st.button("🔍 Evaluate Routing Rules", type="primary", use_container_width=True):
            dept_id, reason, officer_id = routing_svc.route_complaint(
                category_id=cat_map[sel_cat_label],
                ward_id=ward_map[sel_ward_label],
                city=settings.DEFAULT_CITY,
            )
            dept_repo = DepartmentRepository(session)
            dept = dept_repo.get_by_id(dept_id)

            st.success(f"**Target Department:** `{dept.name if dept else dept_id}`")
            st.info(f"**Resolution Path:** {reason}")

# -----------------------------------------------------------------------------
# 3. SLA Calculator
# -----------------------------------------------------------------------------
elif demo_choice == "⏱️ SLA Deadline & Risk Calculator":
    st.markdown("### ⏱️ **SLA Turnaround & Risk Threshold Calculator**")
    st.caption("Calculate target response and resolution turnaround hours by severity:")

    with get_db_session() as session:
        sla_svc = SLAService(session)
        test_sev = st.selectbox("Select Severity Level", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])

        if st.button("📊 Calculate SLA Thresholds", type="primary", use_container_width=True):
            deadline, resp, res = sla_svc.calculate_deadline(category_id=None, severity=test_sev)
            s1, s2, s3 = st.columns(3)
            with s1:
                st.metric("Target Acknowledge Time", f"{resp} Hours")
            with s2:
                st.metric("Target Resolution Time", f"{res} Hours")
            with s3:
                st.metric("Resolution Deadline", deadline.strftime("%d %b %Y, %I:%M %p UTC"))
