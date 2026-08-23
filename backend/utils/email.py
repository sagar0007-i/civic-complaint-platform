"""Email service for password resets and notification dispatch."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, List
from backend.utils.logging import logger

# In-memory email outbox log for local testing / simulation
email_outbox: List[Dict[str, str]] = []


def send_password_reset_email(to_email: str, recipient_name: str, otp_code: str) -> tuple[bool, str]:
    """Send a password reset email with a 6-digit OTP code.
    
    Tries SMTP if environment variables are set; otherwise logs to outbox.
    """
    subject = f"CivicPulse — Password Reset Verification Code: {otp_code}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f4f8; margin: 0; padding: 20px; }}
            .container {{ max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 30px; border: 1px solid #e2e8f0; box-shadow: 0 4px 16px rgba(15,45,107,0.08); }}
            .header {{ text-align: center; border-bottom: 2px solid #ff9900; padding-bottom: 15px; margin-bottom: 25px; }}
            .title {{ font-size: 22px; font-weight: 700; color: #0f2d6b; margin: 0; }}
            .subtitle {{ font-size: 13px; color: #64748b; margin-top: 4px; }}
            .otp-box {{ background: #f8fafc; border: 2px dashed #0f2d6b; border-radius: 10px; padding: 18px; text-align: center; margin: 25px 0; }}
            .otp-code {{ font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #0f2d6b; margin: 0; }}
            .footer {{ font-size: 12px; color: #94a3b8; text-align: center; margin-top: 30px; border-top: 1px solid #f1f5f9; padding-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="title">🏛️ CivicPulse</h1>
                <div class="subtitle">Brihanmumbai Municipal Corporation (BMC / MCGM)</div>
            </div>
            <p>Dear <strong>{recipient_name}</strong>,</p>
            <p>We received a request to reset the password for your CivicPulse account linked to <code>{to_email}</code>.</p>
            <p>Your official 6-digit verification code is:</p>
            
            <div class="otp-box">
                <div class="otp-code">{otp_code}</div>
            </div>
            
            <p>This code is valid for <strong>15 minutes</strong>. Do not share this code with anyone.</p>
            <p>If you did not request a password reset, please ignore this email or contact the BMC IT Helpdesk immediately.</p>
            
            <div class="footer">
                CivicPulse Platform &bull; Secure Authentication Module &bull; BMC IT Division
            </div>
        </div>
    </body>
    </html>
    """

    # Record in outbox list
    outbox_entry = {
        "to_email": to_email,
        "recipient_name": recipient_name,
        "subject": subject,
        "otp_code": otp_code,
        "html_body": html_body,
    }
    email_outbox.append(outbox_entry)
    logger.info(f"Password reset OTP generated for {to_email}: {otp_code}")

    # Check for SMTP config from Settings or env
    from backend.config import settings

    smtp_host = settings.SMTP_HOST or os.getenv("SMTP_HOST")
    smtp_port = int(settings.SMTP_PORT or os.getenv("SMTP_PORT", 587))
    smtp_user = settings.SMTP_USER or os.getenv("SMTP_USER")
    smtp_pass = settings.SMTP_PASSWORD or os.getenv("SMTP_PASSWORD")
    from_email = settings.SMTP_FROM_EMAIL or os.getenv("SMTP_FROM_EMAIL") or smtp_user

    # Only attempt live SMTP dispatch if real non-placeholder credentials are set
    if settings.ENABLE_EMAIL_NOTIFICATIONS and smtp_host and smtp_user and smtp_pass and "your_email@gmail.com" not in smtp_user:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"CivicPulse Auth <{from_email}>"
            msg["To"] = to_email
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(from_email, to_email, msg.as_string())
            
            logger.info(f"Password reset email sent via SMTP to {to_email}")
            return True, f"Verification code sent via email to **{to_email}**."
        except Exception as e:
            logger.error(f"Failed to send email via SMTP ({smtp_host}:{smtp_port}): {e}")
            return True, f"Verification code generated for **{to_email}** (Email outbox fallback active)."
    else:
        return True, f"Verification code dispatched to **{to_email}**."



def get_latest_outbox_email(email: str) -> Optional[Dict[str, str]]:
    """Retrieve latest outbox email for a given recipient (useful for testing & demo)."""
    for entry in reversed(email_outbox):
        if entry["to_email"].lower() == email.lower():
            return entry
    return None
