"""Public Transparency & Civic Analytics Portal."""

import os
import sys
from pathlib import Path
import streamlit as st
import plotly.express as px
import pandas as pd

# Setup Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.database import get_db_session
from backend.services.analytics_service import AnalyticsService
from backend.repositories.department_repo import DepartmentRepository
from backend.repositories.complaint_repo import ComplaintRepository
from backend.utils.session import init_session_state, apply_custom_css
from backend.utils.icons import icon_svg

init_session_state()
apply_custom_css()

st.markdown(f'<h1 class="main-header">{icon_svg("chart", size=28, color="#1E3A8A")} Public Transparency & Analytics</h1>', unsafe_allow_html=True)
st.caption("Open municipal data portal showing grievance trends, resolution velocity, and departmental accountability.")

with get_db_session() as session:
    analytics = AnalyticsService(session)
    dept_repo = DepartmentRepository(session)

    all_depts = dept_repo.get_all(active_only=True)
    dept_map = {d.name: d.id for d in all_depts}

    # Department Filter Bar
    sel_dept_name = st.selectbox("Filter Metrics by Department", ["(All Departments)"] + list(dept_map.keys()))
    sel_dept_id = dept_map.get(sel_dept_name) if sel_dept_name != "(All Departments)" else None

    kpis = analytics.get_summary_kpis(department_id=sel_dept_id)

    # Top KPI Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Reported", f"{kpis['total']:,}")
    m2.metric("In Active Redressal", f"{kpis['in_progress']:,}", delta="In Progress")
    m3.metric("Resolved Issues", f"{kpis['resolved']:,}", delta=f"{kpis['resolution_rate']}% Rate")
    m4.metric("Avg Resolution Time", f"{kpis['avg_resolution_hours']} Hours")

    st.divider()

    # Chart Row 1: Category & Severity Breakdown
    c_col1, c_col2 = st.columns(2)

    with c_col1:
        st.markdown("#### 🗂️ **Grievances by Category**")
        cat_data = analytics.get_category_breakdown(department_id=sel_dept_id)
        if cat_data:
            df_cat = pd.DataFrame(cat_data)
            fig_cat = px.bar(
                df_cat,
                x="count",
                y="category",
                orientation="h",
                color="count",
                color_continuous_scale="Blues",
                labels={"count": "Number of Complaints", "category": "Category"},
            )
            fig_cat.update_layout(yaxis={"autorange": "reversed"}, margin=dict(l=20, r=20, t=20, b=20), height=320)
            st.plotly_chart(fig_cat, width="stretch")
        else:
            st.info("No category data available.")

    with c_col2:
        st.markdown("#### ⚡ **Severity Distribution**")
        sev_data = analytics.get_severity_breakdown()
        if sev_data:
            df_sev = pd.DataFrame(sev_data)
            color_map = {"LOW": "#10B981", "MEDIUM": "#F59E0B", "HIGH": "#F97316", "CRITICAL": "#EF4444"}
            fig_sev = px.pie(
                df_sev,
                values="count",
                names="severity",
                hole=0.45,
                color="severity",
                color_discrete_map=color_map,
            )
            fig_sev.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320)
            st.plotly_chart(fig_sev, width="stretch")
        else:
            st.info("No severity data available.")

    st.divider()

    # Chart Row 2: Ward & Department Load
    w_col1, w_col2 = st.columns(2)

    with w_col1:
        st.markdown("#### 📍 **Grievance Volume by Ward / Zone**")
        ward_data = analytics.get_ward_breakdown()
        if ward_data:
            df_ward = pd.DataFrame(ward_data)
            fig_ward = px.bar(
                df_ward,
                x="ward",
                y="count",
                color="count",
                color_continuous_scale="Teal",
                labels={"ward": "Ward Name", "count": "Complaints"},
            )
            fig_ward.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320)
            st.plotly_chart(fig_ward, width="stretch")
        else:
            st.info("No ward data available.")

    with w_col2:
        st.markdown("#### 🏢 **Department Grievance Workload**")
        dept_data = analytics.get_department_breakdown()
        if dept_data:
            df_dept = pd.DataFrame(dept_data)
            fig_dept = px.pie(
                df_dept,
                values="count",
                names="department",
                labels={"department": "Department", "count": "Grievances"},
            )
            fig_dept.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320)
            st.plotly_chart(fig_dept, width="stretch")
        else:
            st.info("No department data available.")

    st.divider()

    # ── Public SLA Delay & Accountability Register ─────────────────────────
    st.markdown("### 🏛️ **Official Delay Justification & Accountability Register (RTS Act)**")
    st.caption("Public disclosures published by BMC field departments explaining why specific grievances required timeline extensions.")

    comp_repo = ComplaintRepository(session)
    all_complaints = comp_repo.list_complaints(limit=200)

    delayed_complaints = [
        c for c in all_complaints
        if c.delay_reason or (c.sla_deadline and c.status not in ["RESOLVED", "REJECTED"])
    ]

    if delayed_complaints:
        delay_table_data = []
        for c in delayed_complaints:
            delay_table_data.append({
                "Complaint ID": c.complaint_number,
                "Title": c.title,
                "Department": c.department.name if c.department else "N/A",
                "Status": c.status,
                "Official Delay Explanation": c.delay_reason if c.delay_reason else "⚠️ Pending Officer Statement",
                "Accountable Official": c.delay_justified_by or (c.assigned_officer.user.full_name if (c.assigned_officer and c.assigned_officer.user) else "Assigned Department"),
                "Revised Target Date": c.revised_resolution_target.strftime("%d %b %Y") if c.revised_resolution_target else "Accelerated Resolution",
            })
        df_delay = pd.DataFrame(delay_table_data)
        st.dataframe(df_delay, width="stretch", hide_index=True)
    else:
        st.success("✅ All active grievances are currently within committed SLA resolution limits!")

    st.divider()

    # Public Export & SLA Accountability
    st.markdown("### 📥 **Export Public Transparency Report**")
    if all_complaints:
        report_rows = [
            {
                "Complaint ID": c.complaint_number,
                "Title": c.title,
                "Category": c.category.name if c.category else "Uncategorized",
                "Department": c.department.name if c.department else "Unassigned",
                "Ward": c.ward.name if c.ward else "City",
                "Severity": c.severity,
                "Status": c.status,
                "Created At": c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else "",
                "Escalated": "Yes" if c.is_escalated else "No",
                "Delay Reason (Public)": c.delay_reason or "None / Within SLA",
                "Accountable Officer": c.delay_justified_by or "",
                "Revised Target Date": c.revised_resolution_target.strftime("%Y-%m-%d") if c.revised_resolution_target else "",
            }
            for c in all_complaints
        ]
        df_export = pd.DataFrame(report_rows)
        csv_data = df_export.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📊 Download Complete Public Grievance Dataset (CSV)",
            data=csv_data,
            file_name="civicpulse_transparency_data_2026.csv",
            mime="text/csv",
            type="primary",
        )
    else:
        st.info("No complaint data available for export.")

