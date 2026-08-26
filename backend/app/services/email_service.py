"""
Production-grade email service with real Gmail SMTP support.
Sends professional HTML verification and password reset emails.
Falls back to console logging when SMTP is not configured.
"""
import smtplib
import logging
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("versionrag.email")


class EmailService:
    """
    Production email service supporting Gmail SMTP with TLS.
    When SMTP_USER and SMTP_PASSWORD are not set, gracefully falls back
    to logging (development mode).
    """

    @property
    def is_configured(self) -> bool:
        """Check if real SMTP sending is available."""
        return bool(settings.SMTP_USER and settings.SMTP_PASSWORD)

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate a cryptographically secure numeric OTP code."""
        return "".join([str(secrets.randbelow(10)) for _ in range(length)])

    def _send_email(self, to_email: str, subject: str, html_body: str, plain_body: str) -> bool:
        """
        Send an email via Gmail SMTP with TLS.
        Returns True on success, False on failure.
        """
        if not self.is_configured:
            logger.info(
                f"[EMAIL DEV MODE] Would send to {to_email}: {subject}\n"
                f"Plain body preview: {plain_body[:200]}..."
            )
            return True

        from_email = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER
        from_name = settings.EMAILS_FROM_NAME

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email
        msg["Reply-To"] = from_email

        # Attach plain text fallback first, then HTML (preferred)
        part_plain = MIMEText(plain_body, "plain", "utf-8")
        part_html = MIMEText(html_body, "html", "utf-8")
        msg.attach(part_plain)
        msg.attach(part_html)

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(from_email, [to_email], msg.as_string())

            logger.info(f"[EMAIL SENT] Successfully sent '{subject}' to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(
                f"[EMAIL AUTH ERROR] Gmail SMTP authentication failed. "
                f"Ensure you are using a Gmail App Password (not your regular password). "
                f"Error: {e}"
            )
            return False
        except smtplib.SMTPException as e:
            logger.error(f"[EMAIL SMTP ERROR] Failed to send email to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"[EMAIL ERROR] Unexpected error sending to {to_email}: {e}")
            return False

    def send_verification_otp(self, to_email: str, otp_code: str, full_name: str = "there") -> bool:
        """Send a professional verification OTP email."""
        subject = f"🔐 Your VersionRAG Verification Code: {otp_code}"

        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #0a0e17; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0a0e17;">
    <tr>
      <td align="center" style="padding: 40px 20px;">
        <table role="presentation" cellpadding="0" cellspacing="0" width="520" style="max-width: 520px; width: 100%;">

          <!-- Logo Header -->
          <tr>
            <td align="center" style="padding-bottom: 32px;">
              <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background: linear-gradient(135deg, #3b82f6, #6366f1); border-radius: 14px; padding: 12px; line-height: 0;">
                    <img src="https://img.icons8.com/fluency/48/layers.png" alt="V" width="28" height="28" style="display: block;" />
                  </td>
                  <td style="padding-left: 12px; font-size: 22px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;">
                    VersionRAG
                  </td>
                </tr>
              </table>
              <p style="color: #64748b; font-size: 12px; margin: 8px 0 0; letter-spacing: 0.5px;">
                Version-Aware Documentation Intelligence Platform
              </p>
            </td>
          </tr>

          <!-- Main Card -->
          <tr>
            <td style="background-color: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 40px 36px;">

              <!-- Greeting -->
              <h1 style="color: #ffffff; font-size: 20px; font-weight: 700; margin: 0 0 8px; letter-spacing: -0.3px;">
                Verify Your Email Address
              </h1>
              <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin: 0 0 28px;">
                Hi {full_name}, welcome to VersionRAG! Enter the verification code below to activate your account and unlock the full platform.
              </p>

              <!-- OTP Code Box -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding: 24px 0;">
                    <div style="background: linear-gradient(135deg, rgba(59,130,246,0.12), rgba(99,102,241,0.08)); border: 2px solid rgba(59,130,246,0.3); border-radius: 16px; padding: 28px 40px; display: inline-block;">
                      <span style="font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace; font-size: 38px; font-weight: 800; letter-spacing: 14px; color: #60a5fa; text-shadow: 0 0 20px rgba(96,165,250,0.3);">
                        {otp_code}
                      </span>
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Info -->
              <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; margin: 0 0 4px; text-align: center;">
                This code expires in <strong style="color: #f59e0b;">{settings.OTP_EXPIRE_MINUTES} minutes</strong>.
              </p>
              <p style="color: #64748b; font-size: 12px; line-height: 1.5; margin: 0; text-align: center;">
                If you didn't create a VersionRAG account, you can safely ignore this email.
              </p>

            </td>
          </tr>

          <!-- Security Footer -->
          <tr>
            <td style="padding-top: 28px; text-align: center;">
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td style="background-color: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2); border-radius: 12px; padding: 14px 20px;">
                    <p style="color: #fbbf24; font-size: 11px; font-weight: 600; margin: 0 0 4px;">
                      🛡️ Security Notice
                    </p>
                    <p style="color: #94a3b8; font-size: 11px; line-height: 1.5; margin: 0;">
                      Never share your verification code with anyone. VersionRAG staff will never ask for your code or password.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Copyright -->
          <tr>
            <td align="center" style="padding-top: 24px;">
              <p style="color: #475569; font-size: 11px; margin: 0;">
                &copy; 2026 VersionRAG &mdash; Built with version-aware intelligence.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

        plain_body = (
            f"Hi {full_name},\n\n"
            f"Your VersionRAG verification code is: {otp_code}\n\n"
            f"This code expires in {settings.OTP_EXPIRE_MINUTES} minutes.\n\n"
            f"If you didn't create a VersionRAG account, please ignore this email.\n\n"
            f"— VersionRAG Platform"
        )

        return self._send_email(to_email, subject, html_body, plain_body)

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send a professional password reset email."""
        subject = "🔑 VersionRAG — Password Reset Request"

        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #0a0e17; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0a0e17;">
    <tr>
      <td align="center" style="padding: 40px 20px;">
        <table role="presentation" cellpadding="0" cellspacing="0" width="520" style="max-width: 520px; width: 100%;">

          <!-- Logo -->
          <tr>
            <td align="center" style="padding-bottom: 32px;">
              <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background: linear-gradient(135deg, #3b82f6, #6366f1); border-radius: 14px; padding: 12px; line-height: 0;">
                    <img src="https://img.icons8.com/fluency/48/layers.png" alt="V" width="28" height="28" style="display: block;" />
                  </td>
                  <td style="padding-left: 12px; font-size: 22px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;">
                    VersionRAG
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main Card -->
          <tr>
            <td style="background-color: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 40px 36px;">
              <h1 style="color: #ffffff; font-size: 20px; font-weight: 700; margin: 0 0 8px;">
                Reset Your Password
              </h1>
              <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin: 0 0 28px;">
                We received a request to reset your password. Use the token below in your reset form. This token expires in {settings.RESET_TOKEN_EXPIRE_HOURS} hours.
              </p>

              <div style="background: rgba(244,63,94,0.08); border: 1px solid rgba(244,63,94,0.25); border-radius: 12px; padding: 16px; margin-bottom: 20px;">
                <p style="font-family: monospace; font-size: 11px; color: #fda4af; word-break: break-all; margin: 0;">
                  {reset_token}
                </p>
              </div>

              <p style="color: #64748b; font-size: 12px; line-height: 1.5; margin: 0; text-align: center;">
                If you didn't request this reset, you can safely ignore this email. Your password remains unchanged.
              </p>
            </td>
          </tr>

          <tr>
            <td align="center" style="padding-top: 24px;">
              <p style="color: #475569; font-size: 11px; margin: 0;">
                &copy; 2026 VersionRAG &mdash; Built with version-aware intelligence.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

        plain_body = (
            f"Password Reset Request\n\n"
            f"Use this token to reset your password: {reset_token}\n\n"
            f"This token expires in {settings.RESET_TOKEN_EXPIRE_HOURS} hours.\n\n"
            f"If you didn't request this, please ignore this email.\n\n"
            f"— VersionRAG Platform"
        )

        return self._send_email(to_email, subject, html_body, plain_body)

    def send_welcome_email(self, to_email: str, full_name: str) -> bool:
        """Send a welcome email after successful verification."""
        subject = "🎉 Welcome to VersionRAG — Your Account is Verified!"

        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #0a0e17; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0a0e17;">
    <tr>
      <td align="center" style="padding: 40px 20px;">
        <table role="presentation" cellpadding="0" cellspacing="0" width="520" style="max-width: 520px; width: 100%;">

          <!-- Logo -->
          <tr>
            <td align="center" style="padding-bottom: 32px;">
              <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background: linear-gradient(135deg, #3b82f6, #6366f1); border-radius: 14px; padding: 12px; line-height: 0;">
                    <img src="https://img.icons8.com/fluency/48/layers.png" alt="V" width="28" height="28" style="display: block;" />
                  </td>
                  <td style="padding-left: 12px; font-size: 22px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;">
                    VersionRAG
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td style="background-color: #111827; border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 40px 36px; text-align: center;">
              <div style="font-size: 48px; margin-bottom: 16px;">✅</div>
              <h1 style="color: #ffffff; font-size: 22px; font-weight: 700; margin: 0 0 12px;">
                Welcome aboard, {full_name}!
              </h1>
              <p style="color: #94a3b8; font-size: 14px; line-height: 1.7; margin: 0 0 24px;">
                Your email has been verified and your VersionRAG account is now fully active.
                You now have access to version-aware document intelligence, cross-version
                diff analysis, and AI-powered query studios.
              </p>
              <div style="background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(52,211,153,0.08)); border: 1px solid rgba(16,185,129,0.3); border-radius: 12px; padding: 16px;">
                <p style="color: #6ee7b7; font-size: 13px; font-weight: 600; margin: 0;">
                  🚀 Your workspace is ready. Sign in and start exploring!
                </p>
              </div>
            </td>
          </tr>

          <tr>
            <td align="center" style="padding-top: 24px;">
              <p style="color: #475569; font-size: 11px; margin: 0;">
                &copy; 2026 VersionRAG &mdash; Built with version-aware intelligence.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

        plain_body = (
            f"Welcome aboard, {full_name}!\n\n"
            f"Your VersionRAG account has been verified and is now fully active.\n\n"
            f"Sign in and start exploring version-aware document intelligence.\n\n"
            f"— VersionRAG Platform"
        )

        return self._send_email(to_email, subject, html_body, plain_body)

    # Legacy interface kept for backward compatibility
    def send_verification_email(self, to_email: str, token: str):
        """Legacy method — now handled by send_verification_otp."""
        logger.info(f"[EMAIL LEGACY] Verification token for {to_email}: {token}")


email_service = EmailService()
