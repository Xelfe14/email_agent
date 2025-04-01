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

## Local Setup Instructions

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   EMAIL_USERNAME=your_email_username
   EMAIL_PASSWORD=your_email_password
   EMAIL_SMTP_SERVER=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   EMAIL_FALLBACK_TO_DEMO=true # set to false to disable fallback mode
   ```

   ### Gmail Authentication Setup
   If using Gmail with 2-Factor Authentication (which is highly recommended), you must:
   1. Generate an App Password at: https://myaccount.google.com/apppasswords
   2. Select "Mail" as the app and choose a device
   3. Use the generated 16-character password as your EMAIL_PASSWORD
   4. Your regular Gmail password will not work with 2FA enabled

4. Run the app:
   ```
   python -m email_agent.main
   ```

## Streamlit Cloud Deployment

1. Fork this repository to your GitHub account
2. Go to [Streamlit Cloud](https://share.streamlit.io/)
3. Sign in with your GitHub account
4. Click "New app"
5. Select your forked repository
6. Set the main file path to `email_agent/app/main.py`
7. Click "Deploy!"
8. In the app settings, add your secrets:
   - Copy the contents of `.streamlit/secrets.toml.template`
   - Paste them into the Streamlit Cloud secrets manager
   - Replace the placeholder values with your actual credentials

## Demo Mode

The application includes a fallback "Demo Mode" that will simulate email sending when:
- Email authentication fails (wrong username/password)
- SMTP connection errors occur
- Other email sending issues arise

When in Demo Mode:
- Emails are not actually sent to recipients
- The process is simulated and logged
- You'll see "DEMO MODE" in the UI and in logs

To force Demo Mode always, set `EMAIL_FALLBACK_TO_DEMO=true` in your .env file or Streamlit secrets.

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
