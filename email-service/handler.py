"""
HMS Email Service — Serverless Handler
=======================================
A standalone Python serverless function that handles email delivery via
Gmail SMTP. Triggered by HTTP POST from the Django backend.

Supported triggers:
  - SIGNUP_WELCOME       : sent when a new user registers
  - BOOKING_CONFIRMATION : sent when a patient books an appointment

Run locally:
  serverless offline

Django calls:
  POST http://localhost:3001/dev/email/send
  Body: { "trigger": "SIGNUP_WELCOME", "recipient_email": "...", ... }
"""

import json
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ── Gmail SMTP configuration ───────────────────────────────────────────────────
GMAIL_USER: str = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD: str = os.environ.get("GMAIL_APP_PASSWORD", "")
FROM_NAME: str = os.environ.get("FROM_NAME", "HMS Hospital")
SMTP_HOST: str = "smtp.gmail.com"
SMTP_PORT: int = 587


# ── Email template builders ────────────────────────────────────────────────────

def _build_signup_welcome(data: dict) -> tuple[str, str, str]:
    """Returns (subject, plain_text, html) for SIGNUP_WELCOME."""
    name = data.get("recipient_name", "Valued User")
    subject = "Welcome to HMS — Hospital Management System"
    plain = (
        f"Dear {name},\n\n"
        "Welcome to the Hospital Management System (HMS)!\n\n"
        "Your account has been created successfully.\n\n"
        "You can now:\n"
        "  • If you are a Doctor: create availability slots and manage your bookings.\n"
        "  • If you are a Patient: browse doctors, view available slots, and book appointments.\n\n"
        "Thank you for joining HMS.\n\n"
        "Best regards,\n"
        "The HMS Team"
    )
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 40px auto; background: #ffffff;
                  border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.1); }}
    .header {{ background: #2563eb; color: white; padding: 32px 40px; }}
    .header h1 {{ margin: 0; font-size: 24px; }}
    .body {{ padding: 32px 40px; color: #374151; line-height: 1.6; }}
    .footer {{ background: #f9fafb; padding: 20px 40px; color: #6b7280; font-size: 12px; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 8px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🏥 Welcome to HMS</h1>
    </div>
    <div class="body">
      <p>Dear <strong>{name}</strong>,</p>
      <p>Welcome to the <strong>Hospital Management System (HMS)</strong>!</p>
      <p>Your account has been created successfully. Here is what you can do:</p>
      <ul>
        <li><strong>Doctor?</strong> Create availability slots and manage your patient bookings.</li>
        <li><strong>Patient?</strong> Browse doctors, view available slots, and book appointments.</li>
      </ul>
      <p>We are glad to have you on board.</p>
      <p>Best regards,<br><strong>The HMS Team</strong></p>
    </div>
    <div class="footer">
      <p>This is an automated message from HMS. Please do not reply directly to this email.</p>
    </div>
  </div>
</body>
</html>
"""
    return subject, plain, html


def _build_booking_confirmation(data: dict) -> tuple[str, str, str]:
    """Returns (subject, plain_text, html) for BOOKING_CONFIRMATION."""
    name = data.get("recipient_name", "Patient")
    doctor = data.get("doctor_name", "Your Doctor")
    dt = data.get("appointment_datetime", "N/A")

    subject = f"Appointment Confirmed — Dr. {doctor}"
    plain = (
        f"Dear {name},\n\n"
        f"Your appointment has been confirmed!\n\n"
        f"Details:\n"
        f"  Doctor  : Dr. {doctor}\n"
        f"  Date/Time: {dt}\n\n"
        "Please arrive 10 minutes before your appointment time.\n\n"
        "If you need to cancel or reschedule, please contact us as early as possible.\n\n"
        "Best regards,\n"
        "The HMS Team"
    )
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 40px auto; background: #ffffff;
                  border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.1); }}
    .header {{ background: #059669; color: white; padding: 32px 40px; }}
    .header h1 {{ margin: 0; font-size: 24px; }}
    .body {{ padding: 32px 40px; color: #374151; line-height: 1.6; }}
    .info-box {{ background: #ecfdf5; border-left: 4px solid #059669; padding: 16px 20px;
                 border-radius: 4px; margin: 20px 0; }}
    .info-box p {{ margin: 6px 0; }}
    .footer {{ background: #f9fafb; padding: 20px 40px; color: #6b7280; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>✅ Appointment Confirmed</h1>
    </div>
    <div class="body">
      <p>Dear <strong>{name}</strong>,</p>
      <p>Your appointment has been successfully booked. Here are your appointment details:</p>
      <div class="info-box">
        <p><strong>Doctor:</strong> Dr. {doctor}</p>
        <p><strong>Date &amp; Time:</strong> {dt}</p>
      </div>
      <p>Please arrive <strong>10 minutes</strong> before your scheduled time.</p>
      <p>If you need to cancel or reschedule, please contact the clinic at your earliest convenience.</p>
      <p>Best regards,<br><strong>The HMS Team</strong></p>
    </div>
    <div class="footer">
      <p>This is an automated confirmation from HMS. Please do not reply to this email.</p>
    </div>
  </div>
</body>
</html>
"""
    return subject, plain, html


# ── SMTP send helper ───────────────────────────────────────────────────────────

def _send_via_smtp(
    recipient_email: str,
    subject: str,
    plain_text: str,
    html_body: str,
) -> None:
    """Send an email using Gmail SMTP with TLS (port 587)."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise EnvironmentError(
            "GMAIL_USER and GMAIL_APP_PASSWORD environment variables are required."
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{GMAIL_USER}>"
    msg["To"] = recipient_email

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, recipient_email, msg.as_string())

    logger.info("Email sent to %s — subject: %s", recipient_email, subject)


# ── Dispatch table ─────────────────────────────────────────────────────────────

TRIGGER_BUILDERS = {
    "SIGNUP_WELCOME": _build_signup_welcome,
    "BOOKING_CONFIRMATION": _build_booking_confirmation,
}


# ── Lambda / serverless-offline handlers ──────────────────────────────────────

def _json_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def send_email(event: dict, context: Any) -> dict:
    """
    POST /dev/email/send
    Expected JSON body:
      {
        "trigger": "SIGNUP_WELCOME" | "BOOKING_CONFIRMATION",
        "recipient_email": "user@example.com",
        "recipient_name": "John Doe",
        ... trigger-specific fields
      }
    """
    # Parse body — serverless-offline passes body as a string
    try:
        if isinstance(event.get("body"), str):
            data = json.loads(event["body"])
        else:
            data = event.get("body") or {}
    except json.JSONDecodeError:
        return _json_response(400, {"success": False, "message": "Invalid JSON body."})

    # Validate required fields
    trigger = data.get("trigger")
    recipient_email = data.get("recipient_email")

    if not trigger:
        return _json_response(400, {"success": False, "message": "'trigger' is required."})
    if not recipient_email:
        return _json_response(400, {"success": False, "message": "'recipient_email' is required."})

    builder = TRIGGER_BUILDERS.get(trigger)
    if not builder:
        return _json_response(
            400,
            {
                "success": False,
                "message": f"Unknown trigger '{trigger}'. "
                           f"Valid triggers: {list(TRIGGER_BUILDERS.keys())}",
            },
        )

    # Build and send
    try:
        subject, plain_text, html_body = builder(data)
        _send_via_smtp(recipient_email, subject, plain_text, html_body)
        return _json_response(
            200,
            {
                "success": True,
                "message": f"Email sent successfully to {recipient_email}.",
                "trigger": trigger,
            },
        )
    except EnvironmentError as exc:
        logger.error("SMTP not configured: %s", exc)
        return _json_response(
            503,
            {
                "success": False,
                "message": str(exc),
                "hint": "Set GMAIL_USER and GMAIL_APP_PASSWORD in email-service/.env",
            },
        )
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed.")
        return _json_response(
            503,
            {
                "success": False,
                "message": "SMTP authentication failed. Check GMAIL_APP_PASSWORD.",
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Email send failed: %s", exc)
        return _json_response(
            500,
            {"success": False, "message": f"Failed to send email: {str(exc)}"},
        )


def health_check(event: dict, context: Any) -> dict:
    """GET /dev/email/health — liveness probe."""
    return _json_response(
        200,
        {
            "success": True,
            "service": "hms-email-service",
            "status": "healthy",
            "smtp_configured": bool(GMAIL_USER and GMAIL_APP_PASSWORD),
        },
    )
