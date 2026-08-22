"""Media Storage & Validation Tests."""

import io
import pytest
from PIL import Image
from backend.services.storage_service import LocalStorageProvider


def _create_dummy_image_bytes(format="JPEG") -> bytes:
    """Helper to generate real valid image bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color=(73, 109, 137))
    img.save(buf, format=format)
    return buf.getvalue()


def test_valid_image_upload(tmp_path):
    """Test valid JPEG image storage."""
    provider = LocalStorageProvider(base_dir=str(tmp_path))
    img_bytes = _create_dummy_image_bytes("JPEG")

    meta = provider.save_file(
        file_bytes=img_bytes,
        original_filename="pothole_photo.jpg",
        content_type="image/jpeg",
    )

    assert meta is not None
    assert meta["storage_provider"] == "local"
    assert meta["media_type"] == "image"
    assert meta["file_size_bytes"] == len(img_bytes)
    assert meta["file_hash"] is not None

    file_path = provider.get_file_path(meta["storage_path"])
    assert file_path is not None


def test_corrupt_image_rejection(tmp_path):
    """Test fake/corrupt images are rejected."""
    provider = LocalStorageProvider(base_dir=str(tmp_path))
    fake_bytes = b"NOT_A_REAL_IMAGE_DATA_HEADER"

    with pytest.raises(ValueError) as exc:
        provider.save_file(
            file_bytes=fake_bytes,
            original_filename="fake_image.jpg",
            content_type="image/jpeg",
        )
    assert "integrity verification" in str(exc.value)


def test_invalid_extension_rejection(tmp_path):
    """Test disallowed file extensions (.exe, .sh, .py) are rejected."""
    provider = LocalStorageProvider(base_dir=str(tmp_path))
    script_bytes = b"print('malicious')"

    with pytest.raises(ValueError) as exc:
        provider.save_file(
            file_bytes=script_bytes,
            original_filename="malicious.exe",
        )
    assert "Unsupported file extension" in str(exc.value)
