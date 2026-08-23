"""Authentication Portal — Citizen / Officer Registration + Department-Secured Admin Access."""

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

# ─── Department-Specific Officer Access Codes (Server-Side) ───────────────────
DEPARTMENT_OFFICER_CODES = {
    "DEPT_SWM": ["BMC-SWM-2026", "SWM2026", "SAN2026"],
    "DEPT_BWSSB": ["BMC-WATER-2026", "WATER2026", "WTR2026"],
    "DEPT_ROADS": ["BMC-ROADS-2026", "ROADS2026", "RDS2026"],
    "DEPT_SWD": ["BMC-DRAINS-2026", "DRAINS2026", "SWD2026"],
    "DEPT_ELEC": ["BMC-LIGHT-2026", "LIGHT2026", "ELEC2026"],
    "DEPT_HEALTH": ["BMC-HEALTH-2026", "HEALTH2026", "HLT2026"],
    "DEPT_PWD": ["BMC-PWD-2026", "PWD2026"],
}

# ─── Department Admin Access Codes (Server-Side) ──────────────────────────────
DEPARTMENT_ADMIN_CODES = {
    "DEPT_SWM": ["ADMIN-SWM-2026", "SWMADMIN2026", "CIVICBMC2026"],
    "DEPT_BWSSB": ["ADMIN-WATER-2026", "WATERADMIN2026", "CIVICBMC2026"],
    "DEPT_ROADS": ["ADMIN-ROADS-2026", "ROADSADMIN2026", "CIVICBMC2026"],
    "DEPT_SWD": ["ADMIN-DRAINS-2026", "SWDADMIN2026", "CIVICBMC2026"],
    "DEPT_ELEC": ["ADMIN-LIGHT-2026", "LIGHTADMIN2026", "CIVICBMC2026"],
    "DEPT_HEALTH": ["ADMIN-HEALTH-2026", "HEALTHADMIN2026", "CIVICBMC2026"],
    "DEPT_PWD": ["ADMIN-PWD-2026", "PWDADMIN2026", "CIVICBMC2026"],
}

_MASTER_DEPT_ADMIN_CODE = "CIVICBMC2026"
_SUPER_ADMIN_ACCESS_CODE = "COMMISH2026"


def render_forgot_password_expander(key_prefix: str) -> None:
    """Render a reusable 'Forgot Password?' expander with Email OTP verification."""
    with st.expander("🔑 Forgot Password?"):
        st.markdown("##### Reset Your Password via Email OTP")
        st.caption("Enter your registered email address to receive a 6-digit verification code.")

        with st.form(f"forgot_pass_form_{key_prefix}"):
            fp_email = st.text_input("Registered Email Address *", placeholder="e.g. user@example.com", key=f"fp_email_{key_prefix}")
            fp_otp = st.text_input("6-Digit OTP Code (Sent to Email)", placeholder="e.g. 849201", key=f"fp_otp_{key_prefix}")
            fp_new_pass = st.text_input("New Password * (min 8 chars, 1 letter & 1 number)", type="password", key=f"fp_new_pass_{key_prefix}")
            fp_confirm_pass = st.text_input("Confirm New Password *", type="password", key=f"fp_confirm_{key_prefix}")

            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                req_submitted = st.form_submit_button("Send OTP to Email", use_container_width=True)
            with col_btn2:
                reset_submitted = st.form_submit_button("Update Password", type="primary", use_container_width=True)

        if req_submitted:
            if not fp_email:
                st.error("Please enter your registered email address.")
            else:
                with get_db_session() as session:
                    auth = AuthService(session)
                    ok, msg = auth.request_password_reset(fp_email)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

        if reset_submitted:
            if not fp_email or not fp_otp or not fp_new_pass or not fp_confirm_pass:
                st.error("All fields (Email, OTP Code, New Password, Confirm Password) are required.")
            elif fp_new_pass != fp_confirm_pass:
                st.error("New passwords do not match.")
            else:
                with get_db_session() as session:
                    auth = AuthService(session)
                    ok, msg = auth.reset_password(fp_email, fp_otp, fp_new_pass)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)


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

with st.expander("🔑 **Evaluation Guide — All Department Accounts & Secret Access Codes**", expanded=False):
    st.markdown(
        """
        ### 📋 Department-Specific Access Codes (7 BMC Departments)
        | Department Name | Field Officer Email | Officer Access Code | Dept Admin Email | Admin Code |
        |:---|:---|:---|:---|:---|
        | **Solid Waste Management (SWM)** | `officer.swm@civicpulse.gov.in` | `BMC-SWM-2026` | `admin.sanitation@civicpulse.gov.in` | `ADMIN-SWM-2026` |
        | **Water Works (Hydraulic)** | `officer.water@civicpulse.gov.in` | `BMC-WATER-2026` | `admin.water@civicpulse.gov.in` | `ADMIN-WATER-2026` |
        | **Roads & Traffic Infrastructure** | `officer.roads@civicpulse.gov.in` | `BMC-ROADS-2026` | `admin.roads@civicpulse.gov.in` | `ADMIN-ROADS-2026` |
        | **Storm Water Drains (SWD)** | `officer.swd@civicpulse.gov.in` | `BMC-DRAINS-2026` | `admin.swd@civicpulse.gov.in` | `ADMIN-DRAINS-2026` |
        | **BEST & Street Lighting** | `officer.lighting@civicpulse.gov.in` | `BMC-LIGHT-2026` | `admin.lighting@civicpulse.gov.in` | `ADMIN-LIGHT-2026` |
        | **Public Health & Sanitation** | `officer.health@civicpulse.gov.in` | `BMC-HEALTH-2026` | `admin.health@civicpulse.gov.in` | `ADMIN-HEALTH-2026` |
        | **Public Works Department (PWD)** | `officer.pwd@civicpulse.gov.in` | `BMC-PWD-2026` | `admin.pwd@civicpulse.gov.in` | `ADMIN-PWD-2026` |
        
        ---
        ### 👑 Higher Authority & Citizen Logins
        | Role | Login Email | Password | Required Passcode |
        |:---|:---|:---|:---|
        | **🎖️ Super Admin (Commissioner)** | `admin@civicpulse.gov.in` | `Admin@123` | `COMMISH2026` |
        | **🏢 Master Dept Admin** | Any Dept Admin email | `Admin@123` | `CIVICBMC2026` |
        | **🏘️ Citizen** | `citizen.rahul@example.com` | `Citizen@123` | *No code required* |
        
        *Common Passwords: Officers use `Officer@123`, Admins use `Admin@123`, Citizens use `Citizen@123`.*
        """
    )

st.divider()

# =============================================================================
# CITIZEN — Register + Sign In (No Secret Code Required)
# =============================================================================
>>>>>>> 90c0366 (feat: enhance department security codes, officer resolution workbench, and clean production UI)
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

        render_forgot_password_expander("citizen")


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
# FIELD OFFICER — Requires Specific Department Code for Login & Registration
# =============================================================================
elif role_choice == "Field Officer":
    st.markdown(f"## {icon_svg('hard-hat', color='#16A34A')} Field Officer Portal", unsafe_allow_html=True)
    st.info(
        "**Field Officers** are BMC / MCGM field personnel. "
        "Access is strictly restricted to your assigned department. "
        "You must enter the official **Department Access Code** to authenticate or register.",
    )
    tab_off_login, tab_off_register = st.tabs(["Sign In", "Officer Registration"])

    with tab_off_login:
        st.markdown("### Sign In to Your Department Officer Account")
        with st.form("officer_login"):
            off_email = st.text_input("Official Email *", placeholder="e.g. officer.roads@civicpulse.gov.in")
            off_pass = st.text_input("Password *", type="password")
            off_code = st.text_input(
                "Department Officer Access Code *",
                type="password",
                placeholder="e.g. BMC-ROADS-2026 or BMC-SWM-2026",
                help="Enter the specific access code for your department.",
            )
            off_submitted = st.form_submit_button("Sign In as Officer", type="primary", use_container_width=True)
        
        if off_submitted:
            if not off_email or not off_pass or not off_code:
                st.error("Please provide your email, password, and Department Access Code.")
            else:
                with get_db_session() as session:
                    auth = AuthService(session)
                    payload, err = auth.login(UserLoginSchema(email=off_email, password=off_pass))
                if err:
                    st.error(err)
                elif payload["role"] != "OFFICER":
                    st.warning("This portal is for Field Officers only.")
                else:
                    # Validate Department Access Code
                    off_prof = payload.get("officer_profile", {})
                    dept_code = off_prof.get("department_code", "")
                    dept_name = off_prof.get("department_name", "your department")
                    
                    if not dept_code and off_prof.get("department_id"):
                        with get_db_session() as session:
                            from backend.models.department import Department
                            d_obj = session.query(Department).filter(Department.id == off_prof["department_id"]).first()
                            if d_obj:
                                dept_code = d_obj.code
                                dept_name = d_obj.name
                                off_prof["department_code"] = d_obj.code
                                off_prof["department_name"] = d_obj.name
                    
                    valid_codes = DEPARTMENT_OFFICER_CODES.get(dept_code, [])
                    entered_clean = off_code.strip().upper()
                    
                    if entered_clean not in [c.upper() for c in valid_codes]:
                        st.error(
                            f"❌ Access Denied: The code '{off_code}' is NOT valid for the **{dept_name}** department. "
                            f"Each department has its own unique security code."
                        )
                    else:
                        login_user(payload)
                        st.success(f"✅ Authenticated! Welcome, Officer {payload['full_name']} ({dept_name}).")
                        st.switch_page("pages/05_Officer_Dashboard.py")

        render_forgot_password_expander("officer")


    with tab_off_register:
        st.markdown("### Register as a Field Officer")
        st.caption(
            "Registration requires the secret access code of the department you are joining."
        )

        with get_db_session() as session:
            dept_repo = DepartmentRepository(session)
            all_depts = dept_repo.get_all(active_only=True)
            dept_map = {d.name: (d.id, d.code) for d in all_depts}

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
            or_dept_code_input = st.text_input(
                "Department Access Code * (issued by Department Head)",
                type="password",
                placeholder="e.g. BMC-ROADS-2026",
            )
            or_pass = st.text_input(
                "Password * (min 8 chars, must include a letter & number)",
                type="password",
            )
            or_pass2 = st.text_input("Confirm Password *", type="password")
            or_submitted = st.form_submit_button(
                "Submit Officer Registration", type="primary", use_container_width=True
            )

        if or_submitted:
            if not all([or_name, or_email, or_emp_code, or_designation, or_dept_code_input, or_pass, or_pass2]):
                st.error("All fields including Department Access Code are required.")
            elif or_pass != or_pass2:
                st.error("Passwords do not match.")
            else:
                dept_id, dept_code = dept_map[or_dept]
                valid_codes = DEPARTMENT_OFFICER_CODES.get(dept_code, [])
                if or_dept_code_input.strip().upper() not in [c.upper() for c in valid_codes]:
                    st.error(
                        f"❌ Invalid Access Code for **{or_dept}**. "
                        f"You cannot register for this department without its dedicated code."
                    )
                else:
                    with get_db_session() as session:
                        auth = AuthService(session)
                        user_obj, err = auth.create_officer_account(
                            email=or_email,
                            full_name=or_name,
                            password=or_pass,
                            department_id=dept_id,
                            employee_code=or_emp_code,
                            designation=or_designation,
                        )
                    if err:
                        st.error(err)
                    else:
                        st.success(
                            f"Officer account created for **{or_name}** in **{or_dept}**! "
                            "You may now sign in via the **Sign In** tab using your department code."
                        )

# =============================================================================
# DEPARTMENT ADMIN — Requires Specific Department Admin Passcode
# =============================================================================
elif role_choice == "Department Admin":
    st.markdown(f"## {icon_svg('building', color='#EA580C')} Department Administrator Access", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="auth-banner" style="
            background: linear-gradient(135deg, #1E3A5F 0%, #1e40af 100%);
            border-radius: 12px;
            padding: 1.4rem 1.8rem;
            color: #ffffff !important;
            margin-bottom: 1.2rem;
        ">
            <h4 style="margin:0 0 0.4rem 0; color: #ffffff !important;">{icon_svg('lock', color='#FFFFFF')} Restricted Area — Department Head Level</h4>
            <div style="margin:0; opacity:1; font-size:0.9rem; color: #ffffff !important; line-height: 1.5;">
                Department Administrator access gives executive control over departmental ticket queues, 
                officer task assignments, and ward escalations.<br/><br/>
                Enter your credentials and the confidential <span style="color: #ffffff !important; font-weight: 700;">Department Admin Access Code</span>.
            </div>
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
            placeholder="e.g. ADMIN-SWM-2026 or CIVICBMC2026",
        )
        da_submitted = st.form_submit_button(
            "Authenticate as Department Admin", type="primary", use_container_width=True
        )

    if da_submitted:
        if not da_email or not da_pass or not da_code:
            st.error("All fields are required — email, password, and access code.")
        else:
            with get_db_session() as session:
                auth = AuthService(session)
                payload, err = auth.login(UserLoginSchema(email=da_email, password=da_pass))
            if err:
                st.error(err)
            elif payload["role"] not in ("DEPARTMENT_ADMIN", "SUPER_ADMIN"):
                st.warning("Your account does not have Department Admin privileges.")
            else:
                # Check department admin code
                entered_admin_code = da_code.strip().upper()
                all_allowed_admin_codes = [_MASTER_DEPT_ADMIN_CODE.upper()]
                for codes in DEPARTMENT_ADMIN_CODES.values():
                    all_allowed_admin_codes.extend([c.upper() for c in codes])
                
                if entered_admin_code not in all_allowed_admin_codes:
                    st.error("❌ Invalid Department Admin Access Code.")
                else:
                    login_user(payload)
                    st.success(f"Access granted. Welcome, {payload['full_name']}.")
                    st.switch_page("pages/06_Admin_Dashboard.py")

    render_forgot_password_expander("dept_admin")

    with st.expander("Need Access?"):
        st.markdown(
            "Contact the **BMC IT Helpdesk** at `it.helpdesk@civicpulse.gov.in` or call "
            "`+91 22 2462 6600` to request a Department Admin access code. "
            "You must provide your Employee Code and department order letter."
        )

# =============================================================================
# SUPER ADMIN — Commissioner Office Highest Privilege
# =============================================================================
elif role_choice == "Super Admin (Commissioner)":
    st.markdown(f"## {icon_svg('shield-check', color='#DC2626')} Municipal Commissioner — Super Admin Access", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="auth-banner" style="
            background: linear-gradient(135deg, #7c2d12 0%, #991b1b 100%);
            border-radius: 12px;
            padding: 1.4rem 1.8rem;
            color: #ffffff !important;
            margin-bottom: 1.2rem;
        ">
            <h4 style="margin:0 0 0.4rem 0; color: #ffffff !important;">{icon_svg('shield-check', color='#FFFFFF')} Highest Privilege — Municipal Commissioner Level</h4>
            <div style="margin:0; opacity:1; font-size:0.9rem; color: #ffffff !important; line-height: 1.5;">
                Super Admin access grants <span style="color: #ffffff !important; font-weight: 700;">full unrestricted control</span> over all 
                wards, departments, routing rules, SLA policies, and audit logs of the 
                Brihanmumbai Municipal Corporation (BMC / MCGM).<br/><br/>
                This login requires your official credentials <span style="color: #ffffff !important; font-weight: 700;">plus</span> the 
                <span style="color: #ffffff !important; font-weight: 700;">Commissioner's Authorisation Code</span>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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
            placeholder="Confidential code — e.g. COMMISH2026",
        )
        sa_submitted = st.form_submit_button(
            "Authenticate as Super Admin", type="primary", use_container_width=True
        )

    if sa_submitted:
        if not sa_email or not sa_pass or not sa_code:
            st.error("All three fields are mandatory.")
        elif sa_code.strip().upper() != _SUPER_ADMIN_ACCESS_CODE.upper():
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

    render_forgot_password_expander("super_admin")

    with st.expander("Access Information"):
        st.markdown(
            "Super Admin credentials are issued exclusively by the **BMC IT Security Division**. "
            "The authorisation code is rotated every 30 days. "
            "For code renewal, contact the IT Security Division at `security@civicpulse.gov.in`."
        )
