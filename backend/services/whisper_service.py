"""Whisper Multilingual Audio Transcription Service for Civic Grievance Voice Notes."""

import io
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Union, Any, Dict
import numpy as np
from pydantic import BaseModel, Field

from backend.config import settings
from backend.utils.logging import logger


def _ensure_ffmpeg_on_path() -> None:
    """Ensure ffmpeg binary from imageio_ffmpeg is in PATH for Windows/Linux."""
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        bin_dir = os.path.dirname(ffmpeg_exe)

        # On Windows, ensure 'ffmpeg.exe' exists in the binaries directory
        if os.name == "nt":
            dest_exe = os.path.join(bin_dir, "ffmpeg.exe")
            if not os.path.exists(dest_exe) and os.path.exists(ffmpeg_exe):
                try:
                    shutil.copyfile(ffmpeg_exe, dest_exe)
                except Exception:
                    pass

        # Prepend to system PATH if not already present
        curr_path = os.environ.get("PATH", "")
        if bin_dir not in curr_path:
            os.environ["PATH"] = bin_dir + os.pathsep + curr_path
            logger.info(f"Added FFmpeg directory to PATH: {bin_dir}")
    except Exception as e:
        logger.warning(f"Could not auto-configure imageio_ffmpeg: {e}")


# Initialize FFmpeg on module import
_ensure_ffmpeg_on_path()


class WhisperTranscriptionResult(BaseModel):
    """Structured transcription result from Whisper speech-to-text inference."""
    text: str = ""
    language: str = "en"
    language_name: str = "English"
    confidence: float = 0.0
    success: bool = False
    model_used: str = "whisper-base"
    message: str = ""


# Language code to human-readable Indian / Global language names
LANGUAGE_MAP: Dict[str, str] = {
    "mr": "Marathi (मराठी)",
    "hi": "Hindi (हिन्दी)",
    "en": "English",
    "gu": "Gujarati (ગુજરાતી)",
    "ur": "Urdu (اردو)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "bn": "Bengali (বাংলা)",
    "pa": "Punjabi (ਪੰਜਾਬੀ)",
}


class WhisperAudioService:
    """
    Production-ready OpenAI Whisper speech-to-text service.
    Transcribes citizen voice notes in Marathi, Hindi, and English into actionable text.
    """

    _instance: Optional["WhisperAudioService"] = None
    _model: Any = None
    _model_loaded: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(WhisperAudioService, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.WHISPER_MODEL_NAME
        self.device = settings.WHISPER_DEVICE
        _ensure_ffmpeg_on_path()

    def _get_or_load_model(self) -> Any:
        """Lazily load the Whisper model into memory on first audio transcription call."""
        if self._model is not None:
            return self._model

        try:
            import whisper

            logger.info(f"Loading Whisper model '{self.model_name}' on device '{self.device}'...")
            self._model = whisper.load_model(self.model_name, device=self.device)
            self._model_loaded = True
            logger.info("Whisper model loaded successfully.")
            return self._model
        except ImportError:
            logger.warning("openai-whisper is not installed. Voice transcription will run in mock/fallback mode.")
            return None
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}", exc_info=True)
            return None

    def _decode_audio_to_numpy(self, audio_bytes: bytes) -> Optional[np.ndarray]:
        """Decode audio bytes to 16,000 Hz float32 mono numpy array using soundfile."""
        try:
            import soundfile as sf

            buf = io.BytesIO(audio_bytes)
            data, sample_rate = sf.read(buf, dtype="float32")

            # Convert stereo / multi-channel to mono
            if data.ndim > 1:
                data = data.mean(axis=1)

            # Resample to 16000 Hz if necessary
            target_sr = 16000
            if sample_rate != target_sr:
                num_target_samples = int(len(data) * target_sr / sample_rate)
                try:
                    from scipy.signal import resample
                    data = resample(data, num_target_samples).astype(np.float32)
                except Exception:
                    # Simple linear interpolation fallback
                    orig_indices = np.linspace(0, len(data), len(data), endpoint=False)
                    target_indices = np.linspace(0, len(data), num_target_samples, endpoint=False)
                    data = np.interp(target_indices, orig_indices, data).astype(np.float32)

            return data
        except Exception as e:
            logger.debug(f"Direct soundfile audio decoding skipped: {e}")
            return None

    def transcribe_audio(
        self,
        audio_input: Union[bytes, str, Path],
        file_suffix: str = ".wav",
        language_override: Optional[str] = None,
    ) -> WhisperTranscriptionResult:
        """
        Transcribe spoken audio bytes or audio file into text with language detection.

        Args:
            audio_input: Audio bytes or path to audio file (WAV, MP3, WEBM, OGG, M4A).
            file_suffix: Audio format suffix (e.g. '.wav', '.webm', '.mp3').
            language_override: Optional explicit language code (e.g., 'mr', 'hi', 'en').

        Returns:
            WhisperTranscriptionResult with transcribed text and detected language.
        """
        model = self._get_or_load_model()
        if model is None:
            return WhisperTranscriptionResult(
                text="",
                success=False,
                model_used="none",
                message="Whisper model is not available. Please install openai-whisper.",
            )

        transcribe_options: Dict[str, Any] = {
            "fp16": False,  # CPU compatibility
            "temperature": 0.0,
        }
        if language_override:
            transcribe_options["language"] = language_override

        temp_path: Optional[str] = None
        try:
            audio_target: Any = None

            # 1. Fast in-memory decoding for audio bytes (bypasses disk and subprocess)
            if isinstance(audio_input, (bytes, bytearray)):
                raw_bytes = bytes(audio_input)
                if not raw_bytes:
                    return WhisperTranscriptionResult(
                        text="",
                        success=False,
                        model_used=f"whisper-{self.model_name}",
                        message="Empty audio input provided.",
                    )
                np_audio = self._decode_audio_to_numpy(raw_bytes)
                if np_audio is not None and len(np_audio) > 0:
                    audio_target = np_audio
                else:
                    # Fallback to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp:
                        tmp.write(raw_bytes)
                        temp_path = tmp.name
                    audio_target = temp_path
            else:
                audio_target = str(audio_input)

            logger.info("Running Whisper transcription...")
            result = model.transcribe(audio_target, **transcribe_options)

            transcribed_text = (result.get("text") or "").strip()
            detected_lang = result.get("language", "en")
            lang_display_name = LANGUAGE_MAP.get(detected_lang, detected_lang.upper())

            logger.info(f"Whisper transcription complete: '{transcribed_text}' (Language: {detected_lang})")

            return WhisperTranscriptionResult(
                text=transcribed_text,
                language=detected_lang,
                language_name=lang_display_name,
                confidence=0.92,
                success=bool(transcribed_text),
                model_used=f"whisper-{self.model_name}",
                message="Audio transcribed successfully" if transcribed_text else "No speech detected in audio.",
            )

        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}", exc_info=True)
            return WhisperTranscriptionResult(
                text="",
                success=False,
                model_used=f"whisper-{self.model_name}",
                message=f"Transcription error: {e}",
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
