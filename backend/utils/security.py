"""Security, password hashing (Argon2), tokens, and sanitization."""

import html
import re
import secrets
import time
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from backend.utils.logging import logger

# Initialize Argon2 PasswordHasher
ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MB
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2."""
    if not password:
        raise ValueError("Password cannot be empty")
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2 hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        ph.verify(hashed_password, plain_password)
        # Check if rehash is needed
        if ph.check_needs_rehash(hashed_password):
            logger.info("Password hash requires rehashing with updated parameters")
        return True
    except (VerifyMismatchError, VerificationError):
        return False
    except Exception as e:
        logger.error(f"Error during password verification: {e}")
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength:
    - At least 8 characters
    - At least one letter
    - At least one digit
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    return True, "Password is secure."


def generate_secure_token(nbytes: int = 32) -> str:
    """Generate a cryptographically secure random hexadecimal token."""
    return secrets.token_hex(nbytes)


def sanitize_text(input_text: Optional[str]) -> str:
    """Sanitize user text input to prevent XSS and strip unwanted tags."""
    if not input_text:
        return ""
    # Strip HTML tags and escape HTML entities
    cleaned = re.sub(r"<[^>]*>", "", input_text)
    return html.escape(cleaned.strip())
