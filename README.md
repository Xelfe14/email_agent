# AI-Powered Email Agent

An intelligent email processing system that automatically generates personalized responses to inbound emails (e.g., investment pitches) by combining:
- Entity extraction from emails
- Retrieval-augmented generation (RAG) for style matching
- Web search for external context
- LLM-powered response composition
- LangChain AI Agent for email sending
- Human-in-the-loop approval process

## Features

1. **Email Parsing & Entity Extraction**: Extract key information like sender, company, industry, and request.
2. **Parallel Processing**:
   - Style & Context Branch: Find similar historical emails and match tone/style
   - External Data Branch: Gather information about the company/sender from the web
3. **Response Composition**: Intelligently merge style and external data
4. **Human Review & Approval**: Streamlit interface for reviewing and editing responses
5. **LangChain AI Agent for Email Sending**: Utilizes LangChain framework to create an agent that sends emails through SMTP
6. **Send & Log**: Send approved emails and maintain records

## Setup Instructions

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your environment variables in `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   EMAIL_USERNAME=your_email_username
   EMAIL_PASSWORD=your_email_password
   EMAIL_SMTP_SERVER=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   ```

4. Run the app:
   ```
   python -m email_agent.main
   ```

## Testing Email Functionality

To test if your email credentials work correctly:

```
python email_agent/test_email.py
```

This will:
1. Try to send a test email using the direct method
2. Try to send a test email using the LangChain agent

If you see "Email successfully sent" in the output, your email configuration is working correctly.

## Project Structure

- `app/`: Streamlit application files
- `data/`: Sample data and vector stores
- `models/`: Entity extraction and response generation models
- `utils/`:
  - `email_agent.py`: LangChain AI agent for sending emails
  - `email_parser.py`: Email parsing and entity extraction
  - `email_sender.py`: Email sending utilities
  - `rag_retriever.py`: Retrieval-augmented generation
  - `web_research.py`: Web search and data gathering

## Usage

1. Paste an inbound email into the text box
2. Review and edit extracted entities
3. Check the generated response based on historical data and web research
4. Edit the response if needed
5. Click "Approve & Send" to send the email using the LangChain AI agent

## LangChain AI Agent

The system uses LangChain's agent framework to create an intelligent email sending agent that:
- Takes email content, recipient, subject, and CC information
- Uses the OpenAI model to make decisions about email formatting
- Sends the email through SMTP (Gmail by default)
- Provides detailed feedback on the email sending process

This approach allows the system to handle more complex email sending scenarios and provides future extensibility for more advanced email operations.
