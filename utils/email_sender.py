import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

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
        default_sender: str = None,
        sender_name: str = "Sarah Thompson",
        sender_title: str = "Investment Associate",
        company_name: str = "Global Impact Ventures"
    ):
        """
        Initialize the email sender.

        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: Email account username
            password: Email account password
            default_sender: Default sender email address (if different from username)
            sender_name: Name to use in email signature
            sender_title: Title to use in email signature
            company_name: Company name to use in email signature
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.default_sender = default_sender or username
        self.sender_name = "Group 9"
        self.sender_title = "Best Investment Team"
        self.company_name = "Conchita's Impact Ventures"

    def format_email_body(self, body: str) -> str:
        """
        Format the email body with proper HTML structure and signature.

        Args:
            body: Original email body content

        Returns:
            Formatted HTML email body with signature
        """
        # Split paragraphs and add proper spacing
        paragraphs = [p.strip() for p in body.split('\n') if p.strip()]
        formatted_paragraphs = [f"<p style='margin-bottom: 15px; line-height: 1.5;'>{p}</p>" for p in paragraphs]

        # Create signature block
        signature_html = f"""
        <div style='margin-top: 30px; border-top: 1px solid #dddddd; padding-top: 20px;'>
            <p style='margin: 0; color: #333333;'><strong>{self.sender_name}</strong></p>
            <p style='margin: 5px 0; color: #666666;'>{self.sender_title}</p>
            <p style='margin: 5px 0; color: #666666;'>{self.company_name}</p>
        </div>
        """

        # Combine everything in a properly formatted HTML email
        html_email = f"""
        <div style='font-family: Arial, sans-serif; color: #333333; max-width: 600px;'>
            {''.join(formatted_paragraphs)}
            {signature_html}
        </div>
        """

        return html_email

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
        Send an email using SMTP.

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
            print(f"Sending email from {from_address} to {to_address}")
            print(f"Using SMTP server: {self.smtp_server}:{self.smtp_port}")
            print(f"Subject: {subject}")
            print(f"Email body length: {len(body)} characters")

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{from_address}>"
            msg['To'] = to_address

            if cc_addresses:
                msg['Cc'] = ', '.join(cc_addresses)

            # Format the email body with HTML
            formatted_body = self.format_email_body(body) if include_html else body

            # Attach body in both plain text and HTML formats
            if include_html:
                # Plain text version
                plain_text = self._strip_html(body)
                msg.attach(MIMEText(plain_text, 'plain'))
                # HTML version
                msg.attach(MIMEText(formatted_body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            print("Email sent successfully")
            return {
                "status": "success",
                "message": f"Email sent successfully to {to_address}"
            }

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
