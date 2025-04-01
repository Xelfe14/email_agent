from langchain.agents import AgentType, initialize_agent, Tool
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from typing import Dict, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class EmailAgentTool:
    """
    LangChain agent tool for sending emails using SMTP.
    """

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        default_sender: str = None,
        openai_api_key: str = None
    ):
        """
        Initialize the email agent tool.

        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: Email account username
            password: Email account password
            default_sender: Default sender email address (if different from username)
            openai_api_key: OpenAI API key for the agent
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.default_sender = default_sender or username
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        # Initialize the language model
        self.llm = ChatOpenAI(
            temperature=0.0,
            model="gpt-4o",
            api_key=self.openai_api_key
        )

        # Create the agent
        self.agent = self._create_agent()

    def send_email_tool(self, to_address: str, subject: str, body: str, cc_addresses: str = None) -> str:
        """
        Tool for sending an email.

        Args:
            to_address: Recipient email address
            subject: Email subject
            body: Email body content
            cc_addresses: Comma-separated list of CC email addresses

        Returns:
            Status message
        """
        try:
            # Prepare CC addresses
            cc_list = None
            if cc_addresses:
                cc_list = [addr.strip() for addr in cc_addresses.split(',') if addr.strip()]

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.default_sender
            msg["To"] = to_address

            if cc_list:
                msg["Cc"] = ", ".join(cc_list)

            # Add body as plain text and HTML
            plain_text = self._strip_html(body)
            plain_text_part = MIMEText(plain_text, "plain")
            html_part = MIMEText(body, "html")

            msg.attach(plain_text_part)
            msg.attach(html_part)

            # Print debug info
            print(f"Sending email from {msg['From']} to {msg['To']}")
            print(f"Using SMTP server: {self.smtp_server}:{self.smtp_port}")

            # Actually send the email
            all_recipients = [to_address]
            if cc_list:
                all_recipients.extend(cc_list)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)

                server.sendmail(
                    from_addr=msg["From"],
                    to_addrs=all_recipients,
                    msg=msg.as_string()
                )
            return f"Email successfully sent to {to_address}"

        except Exception as e:
            error_message = str(e)
            print(f"Email error: {error_message}")
            return f"Failed to send email: {error_message}"

    def _strip_html(self, html_text: str) -> str:
        """Remove HTML tags for plain text version."""
        import re
        text = re.sub('<[^<]+?>', '', html_text)
        return text

    def _create_agent(self):
        """Create the LangChain agent with email sending capability."""
        tools = [
            Tool(
                name="SendEmail",
                func=self.send_email_tool,
                description="Sends an email to a specified recipient."
            )
        ]

        return initialize_agent(
            tools,
            self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )

    def process_and_send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        cc_addresses: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Process the email request using the LangChain agent and send it.

        Args:
            to_address: Recipient email address
            subject: Email subject
            body: Email body content
            cc_addresses: List of CC email addresses

        Returns:
            Dictionary with status and message
        """
        try:
            # Format CC addresses for the tool
            cc_str = None
            if cc_addresses:
                cc_str = ", ".join(cc_addresses)

            print(f"Attempting to use LangChain agent to send email to {to_address}")

            # Run the agent with appropriate prompt
            agent_prompt = f"""
            Send an email with the following details:
            To: {to_address}
            Subject: {subject}
            {"CC: " + cc_str if cc_str else ""}

            Body:
            {body}

            Use the SendEmail tool with the appropriate parameters.
            """

            response = self.agent.invoke({"input": agent_prompt})

            if "I'll use the SendEmail tool" in response["output"] or "successfully sent" in response["output"]:
                return {
                    "status": "success",
                    "message": response["output"]
                }

            # Fall back to direct method if agent invocation fails
            print("Using direct email sending method")
            result = self.send_email_tool(
                to_address=to_address,
                subject=subject,
                body=body,
                cc_addresses=cc_str
            )

            if "successfully sent" in result:
                return {
                    "status": "success",
                    "message": result
                }
            else:
                return {
                    "status": "error",
                    "message": result
                }

        except Exception as e:
            error_message = str(e)
            print(f"Agent error: {error_message}")
            import traceback
            traceback.print_exc()

            # Try direct method as fallback if agent fails
            try:
                print("Falling back to direct email sending method after error")
                result = self.send_email_tool(
                    to_address=to_address,
                    subject=subject,
                    body=body,
                    cc_addresses=cc_addresses
                )

                if "successfully sent" in result:
                    return {
                        "status": "success",
                        "message": result
                    }
                else:
                    return {
                        "status": "error",
                        "message": result
                    }
            except Exception as inner_e:
                return {
                    "status": "error",
                    "message": f"Failed to send email via agent: {error_message}, Direct method also failed: {str(inner_e)}"
                }

    @classmethod
    def from_env(cls):
        """Create an EmailAgentTool from environment variables."""
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
