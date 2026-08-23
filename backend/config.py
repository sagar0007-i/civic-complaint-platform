"""Application Configuration module using Pydantic Settings."""

import os
from pathlib import Path
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application Settings with environment variable overrides."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core App
    APP_NAME: str = "CivicPulse"
    APP_ENV: Literal["development", "testing", "staging", "production"] = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "civicpulse-secret-key-change-in-production-secure-32chars"

    # Database
    # Default to sqlite:///civic_pulse.db (absolute path) for instant zero-dependency local dev/tests,
    # or postgresql+psycopg://civic_user:civic_pass@localhost:5432/civic_db for Postgres/Docker
    DATABASE_URL: str = Field(
        default=f"sqlite:///{str((BASE_DIR / 'civic_pulse.db').resolve()).replace(chr(92), '/')}",
        description="Database connection string (PostgreSQL or SQLite)",
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # Storage
    STORAGE_PROVIDER: Literal["local", "s3", "r2", "supabase"] = "local"
    STORAGE_LOCAL_DIR: str = str(BASE_DIR / "uploads")
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_IMAGE_EXTENSIONS: set[str] = {"jpg", "jpeg", "png", "webp"}
    ALLOWED_VIDEO_EXTENSIONS: set[str] = {"mp4", "mov", "webm"}
    ALLOWED_IMAGE_MIMES: set[str] = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }
    ALLOWED_VIDEO_MIMES: set[str] = {
        "video/mp4",
        "video/quicktime",
        "video/webm",
    }

    # Cloud Storage S3 / R2 / Supabase
    S3_BUCKET: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_REGION: str = "ap-south-1"
    S3_ENDPOINT_URL: Optional[str] = None

    # AI Service
    AI_PROVIDER: Literal["mock", "heuristic", "gemini", "openai"] = "heuristic"
    AI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # YOLO Pothole Vision AI Model
    YOLO_ENABLED: bool = True
    YOLO_POTHOLE_MODEL_PATH: str = str(BASE_DIR / "ai_models" / "pothole_yolo.pt")
    YOLO_CONFIDENCE_THRESHOLD: float = 0.35
    YOLO_IOU_THRESHOLD: float = 0.45

    # Maps & Location
    MAP_PROVIDER: Literal["osm", "mapbox", "google_maps"] = "osm"
    MAP_API_KEY: Optional[str] = None
    DEFAULT_LATITUDE: float = 19.0760
    DEFAULT_LONGITUDE: float = 72.8777
    DEFAULT_CITY: str = "Mumbai"
    DEFAULT_STATE: str = "Maharashtra"
    DEFAULT_ZOOM: int = 13

    # Notifications
    ENABLE_IN_APP_NOTIFICATIONS: bool = True
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    ENABLE_SMS_NOTIFICATIONS: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "no-reply@civicpulse.gov.in"

    # SLA & Escalations
    SLA_CHECK_INTERVAL_MINUTES: int = 15
    AUTO_ESCALATION_ENABLED: bool = True

    # Duplicate Detection
    DUPLICATE_DISTANCE_METERS_THRESHOLD: float = 150.0  # 150m proximity
    DUPLICATE_DAYS_WINDOW: int = 14  # Active complaints in last 14 days
    DUPLICATE_TEXT_SIMILARITY_THRESHOLD: float = 0.60


settings = Settings()

# Ensure local storage directory exists
os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)
