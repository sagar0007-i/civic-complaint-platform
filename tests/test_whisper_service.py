"""Unit Tests for Whisper Multilingual Voice Transcription Service."""

import pytest
from backend.services.whisper_service import (
    WhisperAudioService,
    WhisperTranscriptionResult,
    LANGUAGE_MAP,
)
from backend.services.ai_service import AIService, HeuristicAIProvider


def test_whisper_service_initialization():
    """Test WhisperAudioService instance attributes."""
    service = WhisperAudioService(model_name="base")
    assert service.model_name == "base"
    assert service.device == "cpu"


def test_whisper_language_map():
    """Test Indian language code mapping."""
    assert LANGUAGE_MAP["mr"] == "Marathi (मराठी)"
    assert LANGUAGE_MAP["hi"] == "Hindi (हिन्दी)"
    assert LANGUAGE_MAP["en"] == "English"
    assert LANGUAGE_MAP["gu"] == "Gujarati (ગુજરાતી)"


def test_whisper_transcription_fallback_empty_audio():
    """Test handling of invalid/empty audio bytes gracefully."""
    service = WhisperAudioService()
    result = service.transcribe_audio(b"")
    assert isinstance(result, WhisperTranscriptionResult)


def test_multilingual_voice_to_category_mapping():
    """Test transcribed Marathi and Hindi text maps to proper categories."""
    ai = AIService(provider=HeuristicAIProvider())

    # 1. Marathi Pothole Grievance
    res_mr_pothole = ai.get_suggestions(
        title="रस्त्यावर खड्डा",
        description="हॉस्पिटलच्या गेट समोर मोठा खड्डा पडला आहे.",
    )
    assert res_mr_pothole["suggested_category_slug"] == "pothole"

    # 2. Marathi Garbage Grievance
    res_mr_garbage = ai.get_suggestions(
        title="कचऱ्याचा ढीग",
        description="गल्लीत खूप कचरा आणि घाण साचली आहे.",
    )
    assert res_mr_garbage["suggested_category_slug"] == "garbage"

    # 3. Hindi Water Leakage Grievance
    res_hi_water = ai.get_suggestions(
        title="पानी की पाइपलाइन",
        description="मेन रोड पर पानी की पाइपलाइन फुट गई है और पानी बह रहा है.",
    )
    assert res_hi_water["suggested_category_slug"] == "water-leakage"

    # 4. Marathi Open Sewage Grievance
    res_mr_sewage = ai.get_suggestions(
        title="गटार ओवरफ्लो",
        description="गटाराचे पाणी रस्त्यावर वाहत आहे आणि दुर्गंधी येत आहे.",
    )
    assert res_mr_sewage["suggested_category_slug"] in ["open-sewage", "public-sanitation"]


def test_voice_transcript_structured_elements():
    """Test intelligent separation of Title, Description, Landmark, and Sector Location."""
    ai = AIService(provider=HeuristicAIProvider())

    # User spoken phrase: "Garbage dump and waste accumulation near the hospital gate at sector 24."
    parsed = ai.parse_voice_transcript("Garbage dump and waste accumulation near the hospital gate at sector 24.")

    assert parsed["suggested_category_slug"] == "garbage"
    assert parsed["landmark"] == "Near Hospital Gate"
    assert "Sector 24" in parsed["address"]
    assert "Near Hospital Gate" in parsed["title"]
    assert "Sector 24" in parsed["title"]
    assert parsed["title"] != parsed["description"]
    assert "Garbage dump and waste accumulation near the hospital gate at sector 24." in parsed["description"]


def test_voice_transcript_area_and_landmark():
    """Test location and landmark extraction from speech without sector number."""
    ai = AIService(provider=HeuristicAIProvider())

    parsed = ai.parse_voice_transcript("Pothole on the road near Dadar railway station.")
    assert parsed["suggested_category_slug"] == "pothole"
    assert "Near Dadar Railway Station" in parsed["landmark"]
    assert parsed["title"] != parsed["description"]


def test_hindi_voice_transcript_kudedaan_sector():
    """Test Hindi grievance parsing with kudedaan, ghar ke aage, and sector 24."""
    ai = AIService(provider=HeuristicAIProvider())

    # User spoken Hindi: "मेरे घर के आगे एक कूड़ेदान है सेक्टर चौबीस"
    # English translation: "There is a dustbin in front of my house at Sector 24."
    parsed = ai.parse_voice_transcript(
        raw_transcript="मेरे घर के आगे एक कूड़ेदान है सेक्टर चौबीस",
        english_translation="There is a dustbin in front of my house at Sector 24.",
    )

    assert parsed["suggested_category_slug"] == "garbage"
    assert "Sector 24" in parsed["address"] or "24" in parsed["address"]
    assert "House" in parsed["landmark"] or "घर" in parsed["landmark"]
    assert parsed["title"] != parsed["description"]
