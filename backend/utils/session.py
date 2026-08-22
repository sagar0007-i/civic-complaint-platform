"""Streamlit Session State, RBAC Guards, and Catchy Modern Civic Theme."""

from typing import Optional, Dict, Any
import streamlit as st
from backend.database import get_db_session
from backend.services.auth_service import AuthService
from backend.models.user import UserRole


def init_session_state() -> None:
    """Initialize default session state keys."""
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "token" not in st.session_state:
        st.session_state.token = None


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return currently logged-in user dictionary."""
    init_session_state()
    return st.session_state.user


def is_logged_in() -> bool:
    """Check if user has an active session."""
    init_session_state()
    return bool(st.session_state.is_authenticated and st.session_state.user)


def get_current_role() -> Optional[str]:
    """Return active user role."""
    init_session_state()
    return st.session_state.role


def login_user(session_payload: Dict[str, Any]) -> None:
    """Store authenticated session in Streamlit state."""
    st.session_state.is_authenticated = True
    st.session_state.user = session_payload
    st.session_state.role = session_payload.get("role")
    st.session_state.token = session_payload.get("token")


def logout_user() -> None:
    """Clear session state and log out."""
    st.session_state.is_authenticated = False
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.token = None


def require_auth(allowed_roles: Optional[list[str]] = None) -> bool:
    """
    Page guard: checks if user is authenticated and authorized.
    Renders login notice if unauthorized.
    """
    init_session_state()
    if not is_logged_in():
        st.warning("🔒 Please log in to access this page.")
        st.info("Navigate to **Login / Register** in the sidebar or use the 1-click demo switcher.")
        return False

    current_role = get_current_role()
    if allowed_roles and current_role not in allowed_roles:
        st.error(f"⛔ Access Denied. This page requires one of the following roles: {', '.join(allowed_roles)}.")
        st.info(f"Your current role is: **{current_role}**.")
        return False

    return True


def apply_custom_css() -> None:
    """Inject catchy, modern, glassmorphic civic styling into Streamlit."""
    custom_css = """
    <style>
    /* Google Fonts Import */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    }

    /* Hero Banner Gradient */
    .hero-banner {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 50%, #0D9488 100%);
        border-radius: 16px;
        padding: 2.2rem 2rem;
        color: white;
        margin-bottom: 1.8rem;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.25);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 0.4rem;
        color: #FFFFFF;
    }
    .civic-icon {
        display: inline-block;
        vertical-align: -0.18em;
        flex: 0 0 auto;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #E0E7FF;
        font-weight: 400;
        max-width: 800px;
        line-height: 1.5;
    }

    /* Evaluation Dossier Card Styling */
    .eval-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-top: 4px solid #2563EB;
        border-radius: 12px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .eval-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .eval-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .eval-subhead {
        font-size: 0.95rem;
        font-weight: 600;
        color: #0F766E;
        margin-top: 0.8rem;
        margin-bottom: 0.3rem;
    }
    .eval-body {
        font-size: 0.9rem;
        color: #334155;
        line-height: 1.6;
    }

    /* Modern Metric Cards */
    .glass-metric {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.1rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }

    /* Pill Badges */
    .pill-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }
    .badge-sub { background-color: #DBEAFE; color: #1E40AF; }
    .badge-prog { background-color: #FEF3C7; color: #92400E; }
    .badge-res { background-color: #D1FAE5; color: #065F46; }
    .badge-crit { background-color: #FEE2E2; color: #991B1B; }

    /* Polished Buttons */
    div.stButton > button:first-child {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.15s ease-in-out;
    }

    /* Timeline Stepper */
    .timeline-node {
        border-left: 3px solid #2563EB;
        padding-left: 1.2rem;
        margin-bottom: 1.2rem;
        position: relative;
    }
    .timeline-node::before {
        content: '';
        position: absolute;
        left: -8px;
        top: 2px;
        width: 13px;
        height: 13px;
        border-radius: 50%;
        background-color: #2563EB;
        border: 2px solid #FFFFFF;
        box-shadow: 0 0 0 2px #BFDBFE;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
