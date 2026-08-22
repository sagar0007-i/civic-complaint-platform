"""Formatting helpers for IDs, timestamps, and UI badges."""

from datetime import datetime, timezone
import random


def generate_complaint_id(year: int | None = None, sequence_num: int | None = None) -> str:
    """
    Generate a standardized unique complaint ID.
    Format: CIV-YYYY-NNNNNN (e.g. CIV-2026-000042)
    """
    if year is None:
        year = datetime.now(timezone.utc).year
    if sequence_num is None:
        sequence_num = random.randint(100000, 999999)
    return f"CIV-{year}-{sequence_num:06d}"


def format_datetime(dt: datetime | None, format_str: str = "%d %b %Y, %I:%M %p") -> str:
    """Format a datetime object into human-readable string."""
    if dt is None:
        return "N/A"
    return dt.strftime(format_str)


def format_status_badge(status: str) -> str:
    """Return status emoji and formatted label."""
    status_map = {
        "SUBMITTED": "📝 Submitted",
        "ACKNOWLEDGED": "👀 Acknowledged",
        "ASSIGNED": "👤 Assigned",
        "IN_PROGRESS": "⚙️ In Progress",
        "WAITING_FOR_INFORMATION": "⏳ Waiting for Info",
        "RESOLVED": "✅ Resolved",
        "REJECTED": "❌ Rejected",
        "REOPENED": "🔄 Reopened",
    }
    return status_map.get(status.upper(), status)


def format_severity_badge(severity: str) -> str:
    """Return severity emoji and formatted label."""
    severity_map = {
        "LOW": "🟢 Low",
        "MEDIUM": "🟡 Medium",
        "HIGH": "🟠 High",
        "CRITICAL": "🔴 Critical",
    }
    return severity_map.get(severity.upper(), severity)
