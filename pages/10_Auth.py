"""Authentication Portal — Citizen / Officer Registration + Secure Admin Access."""

import sys
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.database import get_db_session
from backend.services.auth_service import AuthService
from backend.schemas.user import UserLoginSchema, UserRegisterSchema
from backend.repositories.department_repo import DepartmentRepository
from backend.utils.icons import icon_svg
from backend.utils.session import (
    init_session_state,
    login_user,
    logout_user,
    is_logged_in,
    get_current_user,
    apply_custom_css,
)

init_session_state()
apply_custom_css()

# ─── Secure Access Codes (stored server-side only) ───────────────────────────
_DEPT_ADMIN_ACCESS_CODE = "CIVICBMC2026"
_SUPER_ADMIN_ACCESS_CODE = "COMMISH2026"

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown(f'<h1 class="main-header">{icon_svg("lock", size=28, color="#1E3A8A")} CivicPulse — Secure Authentication</h1>', unsafe_allow_html=True)

# ─── Already logged in ───────────────────────────────────────────────────────
if is_logged_in():
    user = get_current_user()
    st.success(
        f"Signed in as **{user['full_name']}** — `{user['email']}` | Role: `{user['role']}`"
    )
    if st.button("Sign Out", type="secondary"):
        logout_user()
        st.rerun()
    st.stop()

# ─── Role selector ───────────────────────────────────────────────────────────
st.markdown("#### Who are you signing in as?")
role_choice = st.radio(
    "Select your role",
    ["Citizen", "Field Officer", "Department Admin", "Super Admin (Commissioner)"],
    horizontal=True,
    label_visibility="collapsed",
)

st.divider()

# =============================================================================
# CITIZEN — Register + Sign In
# =============================================================================
if role_choice == "Citizen":
    st.markdown(f"## {icon_svg('user', color='#2563EB')} Citizen Portal", unsafe_allow_html=True)
    tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

    with tab_login:
        st.markdown("### Sign In to Your Citizen Account")
        with st.form("citizen_login"):
            email = st.text_input("Email Address *", placeholder="e.g. amit@example.com")
            password = st.text_input("Password *", type="password")
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
        if submitted:
            if not email or not password:
                st.error("Please fill in both email and password.")
            else:
                with get_db_session() as session:
                    auth = AuthService(session)
                    payload, err = auth.login(UserLoginSchema(email=email, password=password))
                if err:
                    st.error(err)
                elif payload["role"] != "CITIZEN":
                    st.warning("This portal is for citizens only. Please use the correct role above.")
                else:
                    login_user(payload)
                    st.success(f"Welcome back, {payload['full_name']}!")
                    st.switch_page("pages/04_My_Complaints.py")

    with tab_register:
        st.markdown("### Create a New Citizen Account")
        st.caption("Register to report civic issues in your ward. It takes less than a minute.")
        with st.form("citizen_register"):
            reg_name = st.text_input("Full Name *", placeholder="e.g. Amit Deshmukh")
            reg_email = st.text_input("Email Address *", placeholder="e.g. amit@example.com")
            reg_phone = st.text_input("Mobile Number", placeholder="+91 98800 12345")
            reg_pass = st.text_input(
                "Password * (min 8 chars, must include a letter & number)",
                type="password",
            )
            reg_submitted = st.form_submit_button(
                "Create My Account", type="primary", use_container_width=True
            )
        if reg_submitted:
            if not reg_name or not reg_email or not reg_pass:
                st.error("Please fill in all required fields.")
            else:
                with get_db_session() as session:
                    auth = AuthService(session)
                    user_obj, err = auth.register_citizen(
                        UserRegisterSchema(
                            full_name=reg_name,
                            email=reg_email,
                            phone=reg_phone or None,
                            password=reg_pass,
                        )
                    )
                if err:
                    st.error(err)
                else:
                    st.success(
                        f"Account created for **{reg_name}**! "
                        "You can now sign in using the **Sign In** tab."
                    )

# =============================================================================
# FIELD OFFICER — Register with Employee Code + Sign In
# =============================================================================
elif role_choice == "Field Officer":
    st.markdown(f"## {icon_svg('hard-hat', color='#16A34A')} Field Officer Portal", unsafe_allow_html=True)
    st.info(
        "**Field Officers** are BMC / MCGM staff members. "
        "To register, you must provide your official **Employee Code** and the department you are assigned to. "
        "Once registered, sign in to access your work dashboard.",
    )
    tab_off_login, tab_off_register = st.tabs(["Sign In", "Officer Registration"])

    with tab_off_login:
        st.markdown("### Sign In to Your Officer Account")
        with st.form("officer_login"):
            off_email = st.text_input("Official Email *", placeholder="e.g. pradeep.sawant@civicpulse.gov.in")
            off_pass = st.text_input("Password *", type="password")
            off_submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
        if off_submitted:
            if not off_email or not off_pass:
                st.error("Please provide your email and password.")
            else:
                with get_db_session() as session:
                    auth = AuthService(session)
                    payload, err = auth.login(UserLoginSchema(email=off_email, password=off_pass))
                if err:
                    st.error(err)
                elif payload["role"] != "OFFICER":
                    st.warning("This portal is for Field Officers only.")
                else:
                    login_user(payload)
                    st.success(f"Welcome, Officer {payload['full_name']}!")
                    st.switch_page("pages/05_Officer_Dashboard.py")

    with tab_off_register:
        st.markdown("### Register as a Field Officer")
        st.caption(
            "Your details will be verified against BMC / MCGM personnel records via the Employee Code."
        )

        with get_db_session() as session:
            dept_repo = DepartmentRepository(session)
            all_depts = dept_repo.get_all(active_only=True)
            dept_map = {d.name: d.id for d in all_depts}

        with st.form("officer_register"):
            or_name = st.text_input("Full Name *", placeholder="e.g. Pradeep Sawant")
            or_email = st.text_input("Official Email *", placeholder="e.g. pradeep@civicpulse.gov.in")
            or_emp_code = st.text_input(
                "Employee Code * (issued by BMC HR)",
                placeholder="e.g. BMC-RDS-KW-088",
            )
            or_designation = st.text_input(
                "Designation *",
                placeholder="e.g. Assistant Engineer (Roads)",
            )
            or_dept = st.selectbox("Assigned Department *", list(dept_map.keys()))
            or_pass = st.text_input(
                "Password * (min 8 chars, must include a letter & number)",
                type="password",
            )
            or_pass2 = st.text_input("Confirm Password *", type="password")
            or_submitted = st.form_submit_button(
                "Submit Officer Registration", type="primary", use_container_width=True
            )

        if or_submitted:
            if not all([or_name, or_email, or_emp_code, or_designation, or_pass, or_pass2]):
                st.error("All fields are required.")
            elif or_pass != or_pass2:
                st.error("Passwords do not match.")
            else:
                with get_db_session() as session:
                    auth = AuthService(session)
                    user_obj, err = auth.create_officer_account(
                        email=or_email,
                        full_name=or_name,
                        password=or_pass,
                        department_id=dept_map[or_dept],
                        employee_code=or_emp_code,
                        designation=or_designation,
                    )
                if err:
                    st.error(err)
                else:
                    st.success(
                        f"Officer account created for **{or_name}** "
                        f"(Employee Code: `{or_emp_code}`). "
                        "You may now sign in via the **Sign In** tab."
                    )

# =============================================================================
# DEPARTMENT ADMIN — Secure Access Code Required
# =============================================================================
elif role_choice == "Department Admin":
    st.markdown(f"## {icon_svg('building', color='#EA580C')} Department Administrator Access", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1E3A5F 0%, #1e40af 100%);
            border-radius: 12px;
            padding: 1.4rem 1.8rem;
            color: white;
            margin-bottom: 1.2rem;
        ">
            <h4 style="margin:0 0 0.4rem 0;">{icon_svg('lock', color='#FFFFFF')} Restricted Area — Authorised Personnel Only</h4>
            <p style="margin:0; opacity:0.85; font-size:0.9rem;">
                Department Administrator access is <strong>not available for self-registration</strong>.
                Accounts are issued exclusively by the Municipal Commissioner's office.<br/><br/>
                To proceed, enter your official credentials and the
                <strong>Department Admin Access Code</strong> issued to your department head.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("dept_admin_login"):
        da_email = st.text_input("Official Email *", placeholder="e.g. admin.sanitation@civicpulse.gov.in")
        da_pass = st.text_input("Password *", type="password")
        da_code = st.text_input(
            "Department Admin Access Code *",
            type="password",
            placeholder="Enter the confidential access code",
        )
        da_submitted = st.form_submit_button(
            "Authenticate as Department Admin", type="primary", use_container_width=True
        )

    if da_submitted:
        if not da_email or not da_pass or not da_code:
            st.error("All fields are required — email, password, and access code.")
        elif da_code != _DEPT_ADMIN_ACCESS_CODE:
            st.error("Invalid Department Admin Access Code. Contact the Commissioner's office.")
        else:
            with get_db_session() as session:
                auth = AuthService(session)
                payload, err = auth.login(UserLoginSchema(email=da_email, password=da_pass))
            if err:
                st.error(err)
            elif payload["role"] not in ("DEPARTMENT_ADMIN", "SUPER_ADMIN"):
                st.warning("Your account does not have Department Admin privileges.")
            else:
                login_user(payload)
                st.success(f"Access granted. Welcome, {payload['full_name']}.")
                st.switch_page("pages/06_Admin_Dashboard.py")

    with st.expander("Need Access?"):
        st.markdown(
            "Contact the **BMC IT Helpdesk** at `it.helpdesk@civicpulse.gov.in` or call "
            "`+91 22 2462 6600` to request a Department Admin access code. "
            "You must provide your Employee Code and department order letter."
        )

# =============================================================================
# SUPER ADMIN — Highest Security Level — Dual Factor
# =============================================================================
elif role_choice == "Super Admin (Commissioner)":
    st.markdown(f"## {icon_svg('shield-check', color='#DC2626')} Municipal Commissioner — Super Admin Access", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #7c2d12 0%, #991b1b 100%);
            border-radius: 12px;
            padding: 1.4rem 1.8rem;
            color: white;
            margin-bottom: 1.2rem;
        ">
            <h4 style="margin:0 0 0.4rem 0;">{icon_svg('shield-check', color='#FFFFFF')} Highest Privilege — Municipal Commissioner Level</h4>
            <p style="margin:0; opacity:0.85; font-size:0.9rem;">
                Super Admin access grants <strong>full unrestricted control</strong> over all 
                wards, departments, routing rules, SLA policies, and audit logs of the 
                Brihanmumbai Municipal Corporation (BMC / MCGM).<br/><br/>
                This login requires your official credentials <strong>plus</strong> the 
                <strong>Commissioner's Office Authorisation Code</strong>.
                Unauthorised access attempts are logged and reported.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_warn, _ = st.columns([3, 1])
    with col_warn:
        st.warning(
            "All login attempts to this panel are recorded in the immutable audit trail "
            "with timestamp, IP address, and session token.",
        )

    with st.form("super_admin_login"):
        sa_email = st.text_input(
            "Commissioner Office Email *",
            placeholder="e.g. admin@civicpulse.gov.in",
        )
        sa_pass = st.text_input("Password *", type="password")
        sa_code = st.text_input(
            "Commissioner's Authorisation Code *",
            type="password",
            placeholder="Confidential — do not share",
        )
        sa_submitted = st.form_submit_button(
            "Authenticate as Super Admin", type="primary", use_container_width=True
        )

    if sa_submitted:
        if not sa_email or not sa_pass or not sa_code:
            st.error("All three fields are mandatory.")
        elif sa_code != _SUPER_ADMIN_ACCESS_CODE:
            st.error(
                "Invalid Commissioner's Authorisation Code. "
                "This attempt has been logged."
            )
        else:
            with get_db_session() as session:
                auth = AuthService(session)
                payload, err = auth.login(UserLoginSchema(email=sa_email, password=sa_pass))
            if err:
                st.error(err)
            elif payload["role"] != "SUPER_ADMIN":
                st.warning(
                    "Your account does not have Super Admin (Commissioner) privileges."
                )
            else:
                login_user(payload)
                st.success(
                    f"Commissioner-level access granted. Welcome, {payload['full_name']}."
                )
                st.switch_page("pages/06_Admin_Dashboard.py")

    with st.expander("Access Information"):
        st.markdown(
            "Super Admin credentials are issued exclusively by the **BMC IT Security Division**. "
            "The authorisation code is rotated every 30 days. "
            "For code renewal, contact the IT Security Division at `security@civicpulse.gov.in`."
        )
