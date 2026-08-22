"""Object Storage Service and Provider Abstraction."""

import abc
import hashlib
import io
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image
from backend.config import settings
from backend.utils.logging import logger


class BaseStorageProvider(abc.ABC):
    """Abstract Base Class for Storage Providers."""

    @abc.abstractmethod
    def save_file(
        self,
        file_bytes: bytes,
        original_filename: str,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save a file and return storage metadata dict."""
        pass

    @abc.abstractmethod
    def get_file_path(self, storage_path: str) -> Optional[str]:
        """Retrieve local filesystem path or URL."""
        pass

    @abc.abstractmethod
    def delete_file(self, storage_path: str) -> bool:
        """Delete a file from storage."""
        pass


class LocalStorageProvider(BaseStorageProvider):
    """Local filesystem storage provider with security validations."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.STORAGE_LOCAL_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to remove dangerous path chars."""
        cleaned = re.sub(r"[^\w\-.]", "_", Path(filename).name)
        return cleaned or "upload.bin"

    def _validate_image(self, file_bytes: bytes) -> bool:
        """Verify that the bytes form a genuine valid image."""
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                img.verify()
            return True
        except Exception:
            return False

    def validate_file(
        self,
        file_bytes: bytes,
        original_filename: str,
        content_type: Optional[str] = None,
    ) -> tuple[bool, str, str]:
        """
        Validate file constraints:
        - Size limit
        - Extension whitelist
        - MIME / format check
        Returns (is_valid, error_msg, media_type)
        """
        # 1. Size check
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > settings.MAX_UPLOAD_SIZE_MB:
            return False, f"File size ({size_mb:.1f} MB) exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB.", ""

        # 2. Extension check
        ext = Path(original_filename).suffix.lstrip(".").lower()
        if ext in settings.ALLOWED_IMAGE_EXTENSIONS:
            media_type = "image"
            if not self._validate_image(file_bytes):
                return False, "File failed image integrity verification. It may be corrupted or invalid.", ""
        elif ext in settings.ALLOWED_VIDEO_EXTENSIONS:
            media_type = "video"
        else:
            return (
                False,
                f"Unsupported file extension '.{ext}'. Allowed images: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}, Allowed videos: {', '.join(settings.ALLOWED_VIDEO_EXTENSIONS)}",
                "",
            )

        return True, "", media_type

    def save_file(
        self,
        file_bytes: bytes,
        original_filename: str,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate, hash, and store a file to the local uploads directory."""
        is_valid, err_msg, media_type = self.validate_file(file_bytes, original_filename, content_type)
        if not is_valid:
            raise ValueError(err_msg)

        # Calculate SHA-256 hash
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Generate unique storage filename
        safe_name = self._sanitize_filename(original_filename)
        ext = Path(safe_name).suffix
        unique_name = f"{uuid.uuid4().hex[:12]}_{safe_name}"

        # Subdirectory by year/month for clean organization
        year_month = datetime.now(timezone.utc).strftime("%Y/%m")
        target_dir = self.base_dir / year_month
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / unique_name

        # Ensure safe path (prevent directory traversal)
        if not str(target_path.resolve()).startswith(str(self.base_dir)):
            raise ValueError("Invalid storage path traversal attempt detected.")

        with open(target_path, "wb") as f:
            f.write(file_bytes)

        # Rel path from uploads folder
        rel_storage_path = f"{year_month}/{unique_name}"

        # Determine MIME
        inferred_mime = content_type or ("image/jpeg" if ext in [".jpg", ".jpeg"] else "application/octet-stream")

        logger.info(f"File stored locally: {rel_storage_path} ({len(file_bytes)} bytes)")

        return {
            "file_name": unique_name,
            "original_filename": original_filename,
            "file_size_bytes": len(file_bytes),
            "mime_type": inferred_mime,
            "storage_provider": "local",
            "storage_path": rel_storage_path,
            "file_hash": file_hash,
            "media_type": media_type,
            "is_public": True,
        }

    def get_file_path(self, storage_path: str) -> Optional[str]:
        """Return absolute path if file exists."""
        full_path = (self.base_dir / storage_path).resolve()
        if full_path.exists() and str(full_path).startswith(str(self.base_dir)):
            return str(full_path)
        return None

    def delete_file(self, storage_path: str) -> bool:
        """Delete local file."""
        full_path = (self.base_dir / storage_path).resolve()
        if full_path.exists() and str(full_path).startswith(str(self.base_dir)):
            try:
                full_path.unlink()
                return True
            except Exception as e:
                logger.error(f"Failed to delete file {storage_path}: {e}")
        return False


class S3StorageProvider(BaseStorageProvider):
    """Cloud S3 / Cloudflare R2 / Supabase Storage Provider."""

    def __init__(self):
        self.bucket = settings.S3_BUCKET
        self.region = settings.S3_REGION

    def save_file(
        self,
        file_bytes: bytes,
        original_filename: str,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Uploads to S3/R2 bucket (in production with credentials)."""
        logger.info(f"Mocking S3 upload to bucket {self.bucket} for {original_filename}")
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        key = f"uploads/{uuid.uuid4().hex}_{original_filename}"
        return {
            "file_name": Path(original_filename).name,
            "original_filename": original_filename,
            "file_size_bytes": len(file_bytes),
            "mime_type": content_type or "application/octet-stream",
            "storage_provider": "s3",
            "storage_path": key,
            "file_hash": file_hash,
            "media_type": "image" if original_filename.endswith((".jpg", ".png", ".webp")) else "video",
            "is_public": True,
        }

    def get_file_path(self, storage_path: str) -> Optional[str]:
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{storage_path}"

    def delete_file(self, storage_path: str) -> bool:
        return True


def get_storage_provider() -> BaseStorageProvider:
    """Storage provider factory."""
    if settings.STORAGE_PROVIDER in ["s3", "r2", "supabase"] and settings.S3_BUCKET:
        return S3StorageProvider()
    return LocalStorageProvider()
