import os
import asyncio
import smtplib
from email.message import EmailMessage


SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)


def _send_email_smtp(to_email: str, subject: str, body: str) -> None:
    """Blocking SMTP send — runs in a worker thread, never on the event loop."""

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


async def send_otp_email(to_email: str, otp: str, expires_minutes: int) -> None:
    subject = "Your Instream verification code"
    body = (
        f"Your verification code is {otp}.\n\n"
        f"It expires in {expires_minutes} minutes. "
        f"If you didn't request this, you can ignore this email."
    )
   
    await asyncio.to_thread(_send_email_smtp, to_email, subject, body)
