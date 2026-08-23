# 🔑 Forgot Password Feature — Setup & Usage Guide

A simple, secure, email-based **Forgot Password** system that allows users to reset their forgotten passwords using a 6-digit OTP code sent directly to their email address.

---

## 🚀 How It Works (3 Easy Steps)

1. **Request OTP**: User enters their registered email address on the Login page under **🔑 Forgot Password?** and clicks **Send OTP to Email**.
2. **Check Email**: The system generates a 6-digit verification OTP code (valid for 15 minutes) and sends it to the user's email inbox.
3. **Set New Password**: User enters the 6-digit OTP code along with their new password and clicks **Update Password**. They can now sign in immediately with their new password.

---

## ⚙️ Setting Up Email Sending (SMTP)

To receive real OTP codes in your **Gmail inbox**, add these lines to your `.env` file in the project folder:

```env
ENABLE_EMAIL_NOTIFICATIONS=True

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
```

### 💡 How to get a Gmail App Password:
1. Go to your **Google Account Settings** ➔ **Security**.
2. Turn on **2-Step Verification** (if not already enabled).
3. Search for **App Passwords** in the search bar.
4. Create a new App Password (name it `CivicPulse`) and copy the 16-character code into `SMTP_PASSWORD`.

---

## 🧪 How to Test Locally

1. Open the application:
   ```bash
   streamlit run app.py
   ```
2. Go to **LOGIN / REGISTER** (`pages/10_Auth.py`).
3. Click on **🔑 Forgot Password?** under any login section.
4. Enter a registered email address (e.g., `parthsalunkhe0103@gmail.com` or `citizen.rahul@example.com`).
5. Click **Send OTP to Email**, enter the code received in your inbox, and update your password!

---

## 🛡️ Security Features

- **OTP Expiration**: OTP codes expire automatically after 15 minutes.
- **Single Use**: Once a password is reset, the OTP code is deleted and cannot be reused.
- **Password Strength**: Requires a minimum of 8 characters, at least 1 letter, and 1 number.
- **Argon2 Hashing**: Passwords are securely hashed before storing in the database.
- **Privacy**: The 6-digit OTP code is never shown on screen—it is delivered privately to the user's email inbox.
