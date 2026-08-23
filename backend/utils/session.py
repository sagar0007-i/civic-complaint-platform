import json
import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
import streamlit as st
from backend.database import get_db_session
from backend.services.auth_service import AuthService
from backend.models.user import UserRole

# File path for persistent session cache
SESSIONS_FILE = Path(__file__).resolve().parent.parent.parent / "uploads" / ".sessions_cache.json"


def _load_sessions_cache() -> Dict[str, Any]:
    """Load active session cache from disk."""
    if not SESSIONS_FILE.exists():
        return {}
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_sessions_cache(data: Dict[str, Any]) -> None:
    """Save active session cache to disk."""
    try:
        SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def init_session_state() -> None:
    """Initialize default session state keys and synchronously restore session from query_params / disk."""
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "token" not in st.session_state:
        st.session_state.token = None

    # Restore session synchronously from query_params on refresh
    if not st.session_state.is_authenticated:
        session_id = st.query_params.get("session")
        if session_id:
            cache = _load_sessions_cache()
            session_payload = cache.get(session_id)
            if session_payload and session_payload.get("user_id") and session_payload.get("role"):
                st.session_state.is_authenticated = True
                st.session_state.user = session_payload
                st.session_state.role = session_payload.get("role")
                st.session_state.token = session_payload.get("token")
                st.session_state.session_id = session_id


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
    """Store authenticated session in Streamlit state and persist synchronously to query_params & disk."""
    session_id = uuid.uuid4().hex[:16]
    st.session_state.is_authenticated = True
    st.session_state.user = session_payload
    st.session_state.role = session_payload.get("role")
    st.session_state.token = session_payload.get("token")
    st.session_state.session_id = session_id

    # Persist session to query_params & disk cache
    try:
        st.query_params["session"] = session_id
        cache = _load_sessions_cache()
        cache[session_id] = session_payload
        _save_sessions_cache(cache)
    except Exception:
        pass


def logout_user() -> None:
    """Clear session state, remove query_param, and purge disk cache."""
    session_id = st.session_state.get("session_id") or st.query_params.get("session")
    if session_id:
        try:
            cache = _load_sessions_cache()
            cache.pop(session_id, None)
            _save_sessions_cache(cache)
        except Exception:
            pass

    try:
        st.query_params.pop("session", None)
    except Exception:
        pass

    st.session_state.is_authenticated = False
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.token = None
    st.session_state.session_id = None


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
    """Inject bold, human-crafted Indian civic design system into Streamlit with guaranteed high contrast."""
    custom_css = """
    <style>
    /* ── Fonts ─────────────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Rajdhani:wght@600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* ── Page Background & Base Text Colors ─────────────────────────────────── */
    .stApp {
        background: #f0f4f8 !important;
        color: #1e293b !important;
    }

    /* Ensure all markdown, paragraphs, and labels in main body are dark and clear */
    .stMain p, .stMain span, .stMain label, .stMain div:not([class*="badge"]):not([class*="hero"]):not([class*="auth-banner"]) {
        color: #1e293b;
    }

    .stMarkdown p:not(.auth-banner *), .stMarkdown strong:not(.auth-banner *) {
        color: #0f2d6b !important;
    }

    /* ── Hero & Auth Banners ────────────────────────────────────────────────── */
    .hero-banner {
        background: linear-gradient(135deg, #0f2d6b 0%, #1a4a9e 40%, #c0392b 100%);
        border-radius: 16px;
        padding: 2.5rem 2.5rem 2.2rem;
        color: #ffffff !important;
        margin-bottom: 1.8rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(15, 45, 107, 0.35);
        border: none;
    }
    .hero-banner *,
    .auth-banner,
    .auth-banner *,
    .auth-banner p,
    .auth-banner strong,
    .auth-banner h1, .auth-banner h2, .auth-banner h3, .auth-banner h4, .auth-banner h5, .auth-banner h6,
    .auth-banner span, .auth-banner div,
    .stMarkdown .auth-banner *,
    .stMarkdown .auth-banner p,
    .stMarkdown .auth-banner strong,
    .stMarkdown .auth-banner h4 {
        color: #ffffff !important;
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: -40px; right: -40px;
        width: 220px; height: 220px;
        background: rgba(255,153,0,0.15);
        border-radius: 50%;
    }
    .hero-banner::after {
        content: '';
        position: absolute;
        bottom: -50px; left: 30%;
        width: 160px; height: 160px;
        background: rgba(255,255,255,0.06);
        border-radius: 50%;
    }
    .hero-title {
        font-family: 'Rajdhani', 'Inter', sans-serif;
        font-size: 2.1rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        margin-bottom: 0.45rem;
        color: #ffffff !important;
        text-shadow: 0 2px 8px rgba(0,0,0,0.25);
        position: relative; z-index: 1;
    }
    .hero-subtitle {
        font-size: 0.97rem;
        color: rgba(255,255,255,0.9) !important;
        font-weight: 400;
        max-width: 780px;
        line-height: 1.65;
        position: relative; z-index: 1;
    }

    /* ── Section Headings ───────────────────────────────────────────────────── */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Rajdhani', 'Inter', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.02em !important;
        color: #0f2d6b !important;
    }

    /* ── Cards (Civic / Role / Eval) ────────────────────────────────────────── */
    .civic-card, .eval-card, .role-card {
        background: #ffffff !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 14px !important;
        padding: 1.4rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 12px rgba(15, 45, 107, 0.07);
        transition: border-color 0.18s, transform 0.18s, box-shadow 0.18s;
    }
    .civic-card:hover, .eval-card:hover, .role-card:hover {
        border-color: #ff9900 !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(15, 45, 107, 0.12);
    }
    .eval-title {
        font-size: 1.12rem;
        font-weight: 700;
        color: #0f2d6b !important;
        margin-bottom: 0.4rem;
    }
    .eval-subhead {
        font-size: 0.91rem;
        font-weight: 600;
        color: #475569 !important;
        margin: 0.6rem 0 0.2rem;
    }
    .eval-body {
        font-size: 0.87rem;
        color: #64748b !important;
        line-height: 1.6;
    }

    /* ── Metric Cards ───────────────────────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 8px rgba(15,45,107,0.06);
        border-top: 4px solid #0f2d6b !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 1.9rem !important;
        font-weight: 700 !important;
        color: #0f2d6b !important;
    }
    [data-testid="stMetricLabel"] {
        font-weight: 600 !important;
        color: #475569 !important;
        font-size: 0.82rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }

    /* ── Sidebar ────────────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f2d6b 0%, #1a3f8f 70%, #0f2d6b 100%) !important;
        border-right: none !important;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown span,
    [data-testid="stSidebar"] label {
        color: #c7d4f0 !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    /* Sidebar nav links */
    [data-testid="stSidebarNav"] a {
        color: #c7d4f0 !important;
        font-weight: 500;
        border-radius: 8px;
        padding: 6px 10px;
        transition: background 0.15s;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255,153,0,0.15) !important;
        color: #ff9900 !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: rgba(255,153,0,0.22) !important;
        color: #ffb733 !important;
        font-weight: 700 !important;
        border-left: 3px solid #ff9900 !important;
    }
    /* Sidebar section group labels */
    [data-testid="stSidebarNav"] span {
        color: rgba(255,153,0,0.9) !important;
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
    }
    /* Sidebar divider */
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.12) !important;
    }
    /* Sidebar logout button */
    [data-testid="stSidebar"] div.stButton > button {
        background: rgba(255,255,255,0.08) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] div.stButton > button:hover {
        background: rgba(255, 80, 60, 0.35) !important;
        border-color: #ff5050 !important;
        color: #ffffff !important;
    }

    /* ── Primary Buttons ────────────────────────────────────────────────────── */
    div.stButton > button[kind="primary"],
    button[data-testid="baseButton-primary"],
    div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #ff9900 0%, #e67e00 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 0.6rem 1.4rem !important;
        box-shadow: 0 4px 14px rgba(255,153,0,0.4) !important;
        letter-spacing: 0.02em !important;
        transition: all 0.18s ease !important;
    }
    div.stButton > button[kind="primary"] *,
    button[data-testid="baseButton-primary"] * {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    div.stButton > button[kind="primary"]:hover,
    button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(135deg, #ffaa1a 0%, #ff9900 100%) !important;
        box-shadow: 0 6px 20px rgba(255,153,0,0.55) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Secondary Buttons ──────────────────────────────────────────────────── */
    div.stButton > button[kind="secondary"],
    button[data-testid="baseButton-secondary"],
    div.stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]) {
        background: #ffffff !important;
        color: #0f2d6b !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.93rem !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
        transition: all 0.15s ease !important;
    }
    div.stButton > button[kind="secondary"] *,
    button[data-testid="baseButton-secondary"] *,
    div.stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]) * {
        color: #0f2d6b !important;
    }
    div.stButton > button[kind="secondary"]:hover,
    div.stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]):hover {
        background: #f0f4ff !important;
        border-color: #ff9900 !important;
        color: #0f2d6b !important;
        box-shadow: 0 2px 8px rgba(255,153,0,0.15) !important;
    }

    /* ── Inputs & Text areas ────────────────────────────────────────────────── */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] > div {
        background-color: #ffffff !important;
        color: #0f2d6b !important;
        border-radius: 10px !important;
        border: 1.5px solid #cbd5e1 !important;
        font-weight: 500 !important;
    }
    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {
        color: #94a3b8 !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: #ff9900 !important;
        box-shadow: 0 0 0 3px rgba(255,153,0,0.15) !important;
    }

    /* ── Status Badges ──────────────────────────────────────────────────────── */
    .badge-critical {
        background: #fef2f2 !important;
        color: #dc2626 !important;
        border: 1px solid #fecaca !important;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .pill-badge {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 3px 10px; border-radius: 9999px;
        font-size: 0.78rem; font-weight: 600;
        background: #f8fafc; color: #1e293b !important;
        border: 1px solid #e2e8f0;
    }
    .dot-indicator { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
    .dot-low, .dot-res  { background: #10b981; }
    .dot-med, .dot-prog { background: #f59e0b; }
    .dot-high, .dot-crit, .dot-sub { background: #ef4444; }

    /* ── Timeline Stepper ───────────────────────────────────────────────────── */
    .timeline-node {
        border-left: 3px solid #ff9900;
        padding-left: 1.2rem;
        margin-bottom: 1.2rem;
        position: relative;
    }
    .timeline-node::before {
        content: '';
        position: absolute; left: -7px; top: 4px;
        width: 11px; height: 11px;
        border-radius: 50%;
        background: #ff9900;
        box-shadow: 0 0 0 3px rgba(255,153,0,0.2);
    }

    /* ── Info / Warning / Success boxes ─────────────────────────────────────── */
    [data-testid="stAlert"] {
        border-radius: 10px !important;
        border-left-width: 4px !important;
        font-weight: 500 !important;
    }

    /* ── Tabs ───────────────────────────────────────────────────────────────── */
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #0f2d6b !important;
        border-bottom: 3px solid #ff9900 !important;
        font-weight: 700 !important;
    }

    /* ── Hide Streamlit Developer Menu, Footer & Decorations (NOT the sidebar toggle) ── */
    /* ── Hide Streamlit Developer Menu, Footer & Toolbar (Preserve Sidebar Control) ── */
    #MainMenu {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    [data-testid="stDecoration"] {visibility: hidden !important; display: none !important;}
    [data-testid="stStatusWidget"] {visibility: hidden !important; display: none !important;}
    .viewerBadge_container__1QSob {visibility: hidden !important; display: none !important;}
    .styles_viewerBadge__1yB5_ {visibility: hidden !important; display: none !important;}
    button[title="View app in Streamlit Community Cloud"] {visibility: hidden !important; display: none !important;}
    #manage-app-button {display: none !important;}

    /* ── Header Container ── */
    [data-testid="stHeader"] {
        background: transparent !important;
        height: 3.5rem !important;
        z-index: 99999 !important;
    }

    /* ── Native Streamlit Sidebar Toggle Control (High-Contrast Civic Styling) ── */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stHeaderNav"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: fixed !important;
        top: 0.6rem !important;
        left: 0.6rem !important;
        z-index: 999999 !important;
    }

    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stHeaderNav"] button,
    button[aria-label="Open sidebar"],
    button[aria-label="Close sidebar"],
    button[aria-label="Toggle sidebar"] {
        background: linear-gradient(135deg, #0f2d6b 0%, #1a4a9e 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        border-radius: 10px !important;
        width: 42px !important;
        height: 42px !important;
        box-shadow: 0 4px 16px rgba(15,45,107,0.45) !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    [data-testid="stSidebarCollapsedControl"] button:hover,
    [data-testid="stSidebarCollapseButton"] button:hover,
    [data-testid="stHeaderNav"] button:hover {
        background: linear-gradient(135deg, #1a4a9e 0%, #ff9900 100%) !important;
        box-shadow: 0 6px 20px rgba(255,153,0,0.4) !important;
        transform: scale(1.05) !important;
    }

    [data-testid="stSidebarCollapsedControl"] button svg,
    [data-testid="stSidebarCollapseButton"] button svg,
    [data-testid="stHeaderNav"] button svg {
        fill: #ffffff !important;
        color: #ffffff !important;
        width: 22px !important;
        height: 22px !important;
    }

    /* ── Responsive Adjustments ── */
    @media screen and (max-width: 768px) {
        [data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            z-index: 9998 !important;
            box-shadow: 6px 0 24px rgba(0,0,0,0.35) !important;
            overflow-y: auto !important;
        }
        .stMainBlockContainer {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 3.5rem !important;
        }
        .hero-banner { padding: 1.5rem 1.2rem !important; }
        .hero-title  { font-size: 1.5rem !important; }
        .hero-subtitle { font-size: 0.88rem !important; }
    }

    @media screen and (min-width: 769px) and (max-width: 1024px) {
        .stMainBlockContainer {
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            padding-top: 3rem !important;
        }
        .hero-title { font-size: 1.75rem !important; }
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
