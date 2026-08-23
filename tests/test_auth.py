"""Authentication & RBAC Unit Tests."""

import pytest
from backend.services.auth_service import AuthService
from backend.schemas.user import UserRegisterSchema, UserLoginSchema
from backend.utils.security import hash_password, verify_password, validate_password_strength


def test_password_hashing_and_verification():
    """Verify Argon2 password hashing and verification."""
    password = "StrongPassword@123"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_password_strength_validator():
    """Verify password strength validation rules."""
    valid, _ = validate_password_strength("ValidPass123")
    assert valid is True

    short_valid, msg = validate_password_strength("Sh1")
    assert short_valid is False
    assert "at least 8 characters" in msg

    no_digit, msg = validate_password_strength("NoDigitsHere")
    assert no_digit is False
    assert "at least one number" in msg


def test_citizen_registration_success(db_session):
    """Test successful citizen self-registration."""
    auth_service = AuthService(db_session)
    reg_data = UserRegisterSchema(
        full_name="Vikram Seth",
        email="vikram.seth@example.com",
        phone="+91 98800 99887",
        password="SecurePassword@123",
    )

    user, err = auth_service.register_citizen(reg_data)
    assert err is None
    assert user is not None
    assert user.email == "vikram.seth@example.com"
    assert user.role == "CITIZEN"


def test_citizen_registration_duplicate_email(db_session, seed_test_data):
    """Test registration fails when email is already taken."""
    auth_service = AuthService(db_session)
    reg_data = UserRegisterSchema(
        full_name="Duplicate User",
        email="citizen.test@example.com",  # Already in seed
        password="SecurePassword@123",
    )

    user, err = auth_service.register_citizen(reg_data)
    assert user is None
    assert "already exists" in err


def test_user_login_success(db_session, seed_test_data):
    """Test login with valid credentials."""
    auth_service = AuthService(db_session)
    login_data = UserLoginSchema(
        email="citizen.test@example.com",
        password="TestPassword@123",
    )

    payload, err = auth_service.login(login_data)
    assert err is None
    assert payload is not None
    assert payload["email"] == "citizen.test@example.com"
    assert payload["role"] == "CITIZEN"
    assert "token" in payload


def test_user_login_invalid_password(db_session, seed_test_data):
    """Test login fails with invalid password."""
    auth_service = AuthService(db_session)
    login_data = UserLoginSchema(
        email="citizen.test@example.com",
        password="WrongPassword999",
    )

    payload, err = auth_service.login(login_data)
    assert payload is None
    assert err == "Invalid email or password."


def test_password_reset_flow(db_session, seed_test_data):
    """Test full password reset via email OTP code."""
    from backend.utils.email import get_latest_outbox_email

    auth_service = AuthService(db_session)
    email = "citizen.test@example.com"

    # 1. Request OTP reset
    ok, msg = auth_service.request_password_reset(email)
    assert ok is True

    outbox_item = get_latest_outbox_email(email)
    assert outbox_item is not None
    otp_code = outbox_item["otp_code"]
    assert len(otp_code) == 6

    # 2. Reset password
    new_pass = "NewSecurePassword@999"
    ok, msg = auth_service.reset_password(email, otp_code, new_pass)
    assert ok is True
    assert "updated successfully" in msg

    # 3. Login with new password
    payload, err = auth_service.login(UserLoginSchema(email=email, password=new_pass))
    assert err is None
    assert payload is not None
    assert payload["email"] == email

