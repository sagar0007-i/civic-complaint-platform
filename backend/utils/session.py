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
    """Inject modern, clean, dark-mode civic styling and high-contrast button styling into Streamlit."""
    custom_css = """
    <style>
    /* Google Fonts Import */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Hero Banner */
    .hero-banner {
        background: #111827;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 2rem 2rem;
        color: #f8fafc;
        margin-bottom: 1.6rem;
    }
    .hero-title {
        font-size: 1.9rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0.35rem;
        color: #f8fafc;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
        font-weight: 400;
        max-width: 800px;
        line-height: 1.55;
    }

    /* Civic & Evaluation Cards */
    .civic-card, .eval-card, .role-card {
        background: #18181b;
        border: 1px solid #27272a;
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: border-color 0.15s ease, transform 0.15s ease;
    }
    .civic-card:hover, .eval-card:hover, .role-card:hover {
        border-color: #3f3f46;
        transform: translateY(-1px);
    }
    .eval-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .eval-subhead {
        font-size: 0.92rem;
        font-weight: 600;
        color: #cbd5e1;
        margin-top: 0.7rem;
        margin-bottom: 0.25rem;
    }
    .eval-body {
        font-size: 0.88rem;
        color: #94a3b8;
        line-height: 1.55;
    }

    /* Metric Cards */
    .glass-metric {
        background: #18181b;
        border: 1px solid #27272a;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }

    /* Minimal Badge Pills with Dot Indicators */
    .pill-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        background: #27272a;
        color: #f8fafc;
        border: 1px solid #3f3f46;
    }
    .dot-indicator {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-low, .dot-res { background-color: #10b981; }
    .dot-med, .dot-prog, .dot-sub { background-color: #f59e0b; }
    .dot-high, .dot-crit { background-color: #f43f5e; }

    /* =========================================================================
       HIGH-CONTRAST VISIBLE BUTTON STYLES
       ========================================================================= */

    /* Primary Buttons (Solid Sharp White with Dark High-Contrast Text) */
    div.stButton > button[kind="primary"],
    div.stButton > button[data-testid="baseButton-primary"],
    button[data-testid="baseButton-primary"],
    button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button[data-testid="baseButton-primary"] {
        background-color: #ffffff !important;
        color: #09090b !important;
        border: 1px solid #ffffff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.55rem 1.25rem !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.25) !important;
        transition: all 0.15s ease-in-out !important;
    }

    /* Force all child text/spans in primary buttons to be dark black */
    div.stButton > button[kind="primary"] *,
    div.stButton > button[data-testid="baseButton-primary"] *,
    button[data-testid="baseButton-primary"] *,
    button[kind="primary"] *,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"] *,
    div[data-testid="stFormSubmitButton"] > button[data-testid="baseButton-primary"] * {
        color: #09090b !important;
        font-weight: 600 !important;
    }

    /* Hover state for primary buttons */
    div.stButton > button[kind="primary"]:hover,
    div.stButton > button[data-testid="baseButton-primary"]:hover,
    button[data-testid="baseButton-primary"]:hover,
    button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button[data-testid="baseButton-primary"]:hover {
        background-color: #e4e4e7 !important;
        color: #09090b !important;
        border-color: #e4e4e7 !important;
        transform: translateY(-1px) !important;
    }

    div.stButton > button[kind="primary"]:hover *,
    div.stButton > button[data-testid="baseButton-primary"]:hover *,
    button[data-testid="baseButton-primary"]:hover *,
    button[kind="primary"]:hover * {
        color: #09090b !important;
    }

    /* Secondary Buttons (Dark Zinc with White High-Contrast Text) */
    div.stButton > button[kind="secondary"],
    div.stButton > button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-secondary"],
    button[kind="secondary"],
    div.stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]) {
        background-color: #18181b !important;
        color: #f8fafc !important;
        border: 1px solid #3f3f46 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        transition: all 0.15s ease-in-out !important;
    }

    div.stButton > button[kind="secondary"] *,
    div.stButton > button[data-testid="baseButton-secondary"] *,
    div.stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]) * {
        color: #f8fafc !important;
    }

    div.stButton > button[kind="secondary"]:hover,
    div.stButton > button[data-testid="baseButton-secondary"]:hover,
    div.stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]):hover {
        background-color: #27272a !important;
        border-color: #71717a !important;
        color: #ffffff !important;
    }

    /* Timeline Stepper */
    .timeline-node {
        border-left: 2px solid #3f3f46;
        padding-left: 1.2rem;
        margin-bottom: 1.2rem;
        position: relative;
    }
    .timeline-node::before {
        content: '';
        position: absolute;
        left: -6px;
        top: 4px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #3b82f6;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
