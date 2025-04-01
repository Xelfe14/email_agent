import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from email_agent.utils.email_agent import EmailAgentTool

class EmailSender:
    """
    Utility for sending email responses.
    """

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        default_sender: str = None
    ):
        """
        Initialize the email sender.

        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: Email account username
            password: Email account password
            default_sender: Default sender email address (if different from username)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.default_sender = default_sender or username

        # Initialize the LangChain email agent
        self.email_agent = EmailAgentTool(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            username=username,
            password=password,
            default_sender=default_sender
        )

    def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        cc_addresses: Optional[list] = None,
        from_address: Optional[str] = None,
        include_html: bool = True
    ) -> Dict[str, Any]:
        """
        Send an email using the LangChain agent.

        Args:
            to_address: Recipient email address
            subject: Email subject
            body: Email body content (can be HTML)
            cc_addresses: List of CC email addresses
            from_address: Sender email address (if different from default)
            include_html: Whether to include HTML formatting

        Returns:
            Dictionary with status and any error message
        """
        try:
            # Ensure to_address is valid or use a default
            if not to_address or '@' not in to_address:
                to_address = "danielle@pawlife.co"  # Use default recipient if none provided

            # Ensure from_address is valid
            if not from_address or '@' not in from_address:
                from_address = self.default_sender

            # Print debug info
            print(f"Sending email via LangChain agent from {from_address} to {to_address}")
            print(f"Using SMTP server: {self.smtp_server}:{self.smtp_port}")
            print(f"Subject: {subject}")
            print(f"Email body length: {len(body)} characters")

            # Use the LangChain agent to send the email
            result = self.email_agent.process_and_send_email(
                to_address=to_address,
                subject=subject,
                body=body,
                cc_addresses=cc_addresses
            )

            # Log the result for debugging
            print(f"Email sending result: {result}")

            # Return result
            return result

        except Exception as e:
            error_message = str(e)
            print(f"Email error: {error_message}")

            # Print more detailed traceback
            import traceback
            traceback.print_exc()

            return {
                "status": "error",
                "message": f"Failed to send email: {error_message}"
            }

    def _strip_html(self, html_text: str) -> str:
        """
        Remove HTML tags for plain text version.

        Args:
            html_text: Text with potential HTML tags

        Returns:
            Plain text without HTML tags
        """
        # This is a very simple implementation
        # A more robust solution would use a library like BeautifulSoup
        import re
        text = re.sub('<[^<]+?>', '', html_text)
        return text

    @classmethod
    def from_env(cls):
        """
        Create an EmailSender from environment variables.

        Environment variables needed:
        - EMAIL_SMTP_SERVER
        - EMAIL_SMTP_PORT
        - EMAIL_USERNAME
        - EMAIL_PASSWORD
        - EMAIL_DEFAULT_SENDER (optional)

        Returns:
            EmailSender instance
        """
        smtp_server = os.environ.get("EMAIL_SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", 587))
        username = os.environ.get("EMAIL_USERNAME", "b2b.cik.corp@gmail.com")
        password = os.environ.get("EMAIL_PASSWORD", "pepelotteadroitepepelotteagauche1114")
        default_sender = os.environ.get("EMAIL_DEFAULT_SENDER", username)

        if not all([smtp_server, username, password]):
            raise ValueError("Missing required environment variables for email sending")

        return cls(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            username=username,
            password=password,
            default_sender=default_sender
        )
