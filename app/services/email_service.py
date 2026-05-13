# app/services/email_service.py

import logging
from pathlib import Path
from typing import Optional

from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from pydantic import EmailStr

from app.config import settings

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------
# Mail Connection Config
# ----------------------------------------------------------------

mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fastmail = FastMail(mail_config)


# ----------------------------------------------------------------
# Email Templates (inline HTML)
# ----------------------------------------------------------------

def _verification_email_html(full_name: str, verification_link: str) -> str:
    """
    Returns HTML body for email verification email.

    Args:
        full_name: Recipient's full name.
        verification_link: Full URL with verification token.

    Returns:
        HTML string.
    """
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: auto; padding: 32px;">
          <h2 style="color: #1a1a2e;">Welcome to LegalLens, {full_name}!</h2>
          <p>Thank you for registering. Please verify your email address to activate your account.</p>
          <div style="text-align: center; margin: 32px 0;">
            <a href="{verification_link}"
               style="background-color: #4f46e5; color: white; padding: 14px 28px;
                      text-decoration: none; border-radius: 6px; font-size: 16px;">
              Verify Email Address
            </a>
          </div>
          <p style="color: #666; font-size: 13px;">
            This link expires in <strong>24 hours</strong>.<br>
            If you did not create a LegalLens account, you can safely ignore this email.
          </p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
          <p style="color: #999; font-size: 12px;">
            &copy; LegalLens. All rights reserved.
          </p>
        </div>
      </body>
    </html>
    """


def _password_reset_email_html(full_name: str, reset_link: str) -> str:
    """
    Returns HTML body for password reset email.

    Args:
        full_name: Recipient's full name.
        reset_link: Full URL with password reset token.

    Returns:
        HTML string.
    """
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: auto; padding: 32px;">
          <h2 style="color: #1a1a2e;">Password Reset Request</h2>
          <p>Hi {full_name}, we received a request to reset your LegalLens password.</p>
          <div style="text-align: center; margin: 32px 0;">
            <a href="{reset_link}"
               style="background-color: #dc2626; color: white; padding: 14px 28px;
                      text-decoration: none; border-radius: 6px; font-size: 16px;">
              Reset My Password
            </a>
          </div>
          <p style="color: #666; font-size: 13px;">
            This link expires in <strong>1 hour</strong>.<br>
            If you did not request a password reset, please ignore this email.
            Your password will not be changed.
          </p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
          <p style="color: #999; font-size: 12px;">
            &copy; LegalLens. All rights reserved.
          </p>
        </div>
      </body>
    </html>
    """


# ----------------------------------------------------------------
# Send Email Verification
# ----------------------------------------------------------------

async def send_verification_email(
    email: EmailStr,
    full_name: str,
    token: str,
) -> None:
    """
    Sends an email verification link to a newly registered user.

    Args:
        email: Recipient email address.
        full_name: Recipient's full name for personalization.
        token: Secure verification token to embed in the link.

    Raises:
        Exception: If the email fails to send (logged, not swallowed).
    """
    verification_link = (
        f"{settings.FRONTEND_URL}/verify-email?token={token}"
    )

    message = MessageSchema(
        subject="Verify your LegalLens account",
        recipients=[email],
        body=_verification_email_html(full_name, verification_link),
        subtype=MessageType.html,
    )

    try:
        await fastmail.send_message(message)
        logger.info(f"Verification email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {e}")
        raise


# ----------------------------------------------------------------
# Send Password Reset Email
# ----------------------------------------------------------------

async def send_password_reset_email(
    email: EmailStr,
    full_name: str,
    token: str,
) -> None:
    """
    Sends a password reset link to the user.

    Args:
        email: Recipient email address.
        full_name: Recipient's full name for personalization.
        token: Secure password reset token to embed in the link.

    Raises:
        Exception: If the email fails to send (logged, not swallowed).
    """
    reset_link = (
        f"{settings.FRONTEND_URL}/reset-password?token={token}"
    )

    message = MessageSchema(
        subject="Reset your LegalLens password",
        recipients=[email],
        body=_password_reset_email_html(full_name, reset_link),
        subtype=MessageType.html,
    )

    try:
        await fastmail.send_message(message)
        logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {e}")
        raise