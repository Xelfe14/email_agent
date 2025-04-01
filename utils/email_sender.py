import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import os

def send_email_agent(
    recipient_email: str,
    subject: str,
    body: str,
    sender_email: Optional[str] = None,
    sender_password: Optional[str] = None,
    smtp_server: Optional[str] = None,
    smtp_port: Optional[int] = None
) -> bool:
    """
    Send an email using the configured SMTP settings.

    Args:
        recipient_email: Email address of the recipient
        subject: Email subject
        body: Email body content
        sender_email: Optional sender email (defaults to environment variable)
        sender_password: Optional sender password (defaults to environment variable)
        smtp_server: Optional SMTP server (defaults to environment variable)
        smtp_port: Optional SMTP port (defaults to environment variable)

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Use environment variables if not provided
        sender_email = sender_email or os.getenv("EMAIL_DEFAULT_SENDER")
        sender_password = sender_password or os.getenv("EMAIL_PASSWORD")
        smtp_server = smtp_server or os.getenv("EMAIL_SMTP_SERVER")
        smtp_port = int(smtp_port or os.getenv("EMAIL_SMTP_PORT", "587"))

        if not all([sender_email, sender_password, smtp_server, smtp_port]):
            raise ValueError("Missing required email configuration")

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        # Add body
        msg.attach(MIMEText(body, 'plain'))

        # Create SMTP session
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return True

    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False
