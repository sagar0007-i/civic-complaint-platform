"""AI Abstraction and Heuristic NLP Unit Tests."""

import pytest
from backend.services.ai_service import AIService, HeuristicAIProvider


def test_ai_heuristic_category_classification():
    """Test AI categorizes complaint from raw text."""
    ai = AIService(provider=HeuristicAIProvider())

    sugg_pothole = ai.get_suggestions(
        title="Huge pothole on main road",
        description="Deep road asphalt crater causing damage to bikes.",
    )
    assert sugg_pothole["suggested_category_slug"] == "pothole"

    sugg_sewage = ai.get_suggestions(
        title="Open sewage overflowing",
        description="Black water from blocked drain line spilling onto footpath.",
    )
    assert sugg_sewage["suggested_category_slug"] == "open-sewage"


def test_ai_heuristic_severity_estimation():
    """Test AI estimates severity level accurately."""
    provider = HeuristicAIProvider()

    crit_sev = provider.estimate_severity("Open manhole posing severe hazard to children.")
    assert crit_sev == "CRITICAL"

    med_sev = provider.estimate_severity("Garbage bin needs clearing.")
    assert med_sev in ["MEDIUM", "LOW"]


def test_ai_officer_summary_generation():
    """Test AI summary generation."""
    ai = AIService()
    res = ai.get_suggestions(
        title="Broken streetlight",
        description="Streetlight has been dark for 3 days near the hospital gate.",
        landmark="Near Manipal Hospital",
    )
    assert "Broken streetlight" in res["summary_text"]
    assert "Near Manipal Hospital" in res["summary_text"]
