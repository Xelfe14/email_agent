import re
from typing import Dict, Any, Tuple
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

def extract_entities(email_text: str, api_key: str) -> Dict[str, Any]:
    """
    Extract entities from email text using the EmailParser class.

    Args:
        email_text: The text of the email to parse
        api_key: OpenAI API key

    Returns:
        Dictionary of extracted entities
    """
    parser = EmailParser(api_key)
    return parser.parse_email(email_text)

class EmailParser:
    """
    Extracts structured information from email text using LLM.
    """

    def __init__(self, api_key: str):
        """
        Initialize the email parser with OpenAI API key.

        Args:
            api_key: OpenAI API key
        """
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0,
            api_key=api_key
        )

        # Define the schemas for structured extraction
        self.response_schemas = [
            ResponseSchema(name="sender_name", description="The full name of the email sender"),
            ResponseSchema(name="sender_email", description="The email address of the sender"),
            ResponseSchema(name="company_name", description="The company or organization the sender represents"),
            ResponseSchema(name="industry", description="The industry or sector the company operates in"),
            ResponseSchema(name="funding_stage", description="If mentioned, the funding stage of the company (e.g., seed, Series A)"),
            ResponseSchema(name="ask_amount", description="The amount of funding requested, if specified"),
            ResponseSchema(name="request_summary", description="A brief summary of what the sender is asking for"),
            ResponseSchema(name="key_points", description="List of key points mentioned in the email"),
            ResponseSchema(name="founders", description="Names of founders mentioned in the email"),
            ResponseSchema(name="location", description="Location of the company if mentioned"),
            ResponseSchema(name="website", description="Company website if mentioned"),
        ]

        self.output_parser = StructuredOutputParser.from_response_schemas(self.response_schemas)
        self.format_instructions = self.output_parser.get_format_instructions()

        self.template = """
        Extract the following information from the email below. If a piece of information is not present, write 'Not mentioned'.

        {format_instructions}

        EMAIL:
        {email_text}

        EXTRACTED INFORMATION:
        """

        self.prompt = ChatPromptTemplate.from_template(self.template)

    def parse_email(self, email_text: str) -> Dict[str, Any]:
        """
        Parse email text and extract structured information.

        Args:
            email_text: The full text of the email to parse

        Returns:
            Dictionary of extracted entities
        """
        # First try to extract email directly from headers if present
        sender_email = self._extract_email_from_headers(email_text)

        # Extract email parts if it includes headers
        clean_text, headers = self._clean_email_text(email_text)

        # Extract structured information using LLM
        chain = self.prompt | self.llm | self.output_parser
        extracted_info = chain.invoke({
            "format_instructions": self.format_instructions,
            "email_text": clean_text
        })

        # If we found an email in the headers, make sure it's used
        if sender_email and (not extracted_info.get('sender_email') or extracted_info.get('sender_email') == 'Not mentioned'):
            extracted_info['sender_email'] = sender_email

        return extracted_info

    def _extract_email_from_headers(self, email_text: str) -> str:
        """
        Extract sender email from email headers.

        Args:
            email_text: Raw email text with potential headers

        Returns:
            Sender email address if found, empty string otherwise
        """
        # Look for From: header with email pattern
        from_header_pattern = r"From:.*?[\[\<]?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})[\]\>]?"
        from_match = re.search(from_header_pattern, email_text)

        if from_match:
            return from_match.group(1)

        # Look for Reply-To header
        reply_to_pattern = r"Reply-To:.*?[\[\<]?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})[\]\>]?"
        reply_match = re.search(reply_to_pattern, email_text)

        if reply_match:
            return reply_match.group(1)

        # Look for any email pattern in the first few lines
        email_pattern = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"

        # Check first 10 lines
        first_lines = "\n".join(email_text.split("\n")[:10])
        email_match = re.search(email_pattern, first_lines)

        if email_match:
            return email_match.group(1)

        return ""

    def _clean_email_text(self, email_text: str) -> Tuple[str, Dict[str, str]]:
        """
        Clean the email text by removing headers, signatures, etc.

        Args:
            email_text: Raw email text

        Returns:
            Tuple of (cleaned email text, headers dictionary)
        """
        headers = {}

        # Extract headers if present
        if re.search(r"From:|To:|Subject:|Date:", email_text):
            # Split headers and body
            parts = re.split(r"\n\n|\r\n\r\n", email_text, 1)

            if len(parts) > 1:
                header_text, body = parts
                # Parse headers
                for line in header_text.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        headers[key.strip().lower()] = value.strip()

                email_text = body

        # Try to remove signatures
        signature_patterns = [
            r"--\s*\n.*",  # Standard signature delimiter
            r"Kind(\s+)regards,[\s\S]*$",
            r"Best(\s+)regards,[\s\S]*$",
            r"Sincerely,[\s\S]*$",
            r"Thanks,[\s\S]*$",
            r"Thank(\s+)you,[\s\S]*$",
        ]

        for pattern in signature_patterns:
            email_text = re.sub(pattern, "", email_text, flags=re.IGNORECASE)

        return email_text.strip(), headers
