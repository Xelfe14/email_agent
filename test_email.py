#!/usr/bin/env python
"""
Test script for validating email sending functionality.
"""
import os
from dotenv import load_dotenv
from email_agent.utils.email_agent import EmailAgentTool

# Load environment variables
load_dotenv()

def test_direct_email_send():
    """Test direct email sending using EmailAgentTool."""
    agent = EmailAgentTool(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="b2b.cik.corp@gmail.com",
        password="pepelotteadroitepepelotteagauche1114",
        default_sender="b2b.cik.corp@gmail.com"
    )

    print("Testing direct email sending...")
    result = agent.send_email_tool(
        to_address="test@example.com",
        subject="Test Email from Agent",
        body="<p>This is a test email from the LangChain email agent.</p>"
    )

    print(f"Result: {result}")

if __name__ == "__main__":
    test_direct_email_send()
