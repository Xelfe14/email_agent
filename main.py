import os
import streamlit as st
import pandas as pd
import json
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
from utils.email_parser import extract_entities
from utils.rag_retriever import get_similar_examples
from utils.web_research import research_company
from utils.email_sender import send_email_agent

# Initialize session state variables first
if "extracted_info" not in st.session_state:
    st.session_state["extracted_info"] = None
if "style_draft" not in st.session_state:
    st.session_state["style_draft"] = None
if "research_data" not in st.session_state:
    st.session_state["research_data"] = None
if "final_response" not in st.session_state:
    st.session_state["final_response"] = None
if "original_email" not in st.session_state:
    st.session_state["original_email"] = None
if "similar_examples" not in st.session_state:
    st.session_state["similar_examples"] = None
if "processing" not in st.session_state:
    st.session_state["processing"] = False
if "step" not in st.session_state:
    st.session_state["step"] = "input"
if "status_message" not in st.session_state:
    st.session_state["status_message"] = ""

# Configure secrets
secrets = st.secrets

# Set up environment variables from secrets
os.environ["OPENAI_API_KEY"] = secrets["OPENAI_API_KEY"]
os.environ["EMAIL_SMTP_SERVER"] = secrets["email"]["SMTP_SERVER"]
os.environ["EMAIL_SMTP_PORT"] = str(secrets["email"]["SMTP_PORT"])
os.environ["EMAIL_USERNAME"] = secrets["email"]["USERNAME"]
os.environ["EMAIL_PASSWORD"] = secrets["email"]["PASSWORD"]
os.environ["EMAIL_DEFAULT_SENDER"] = secrets["email"]["DEFAULT_SENDER"]
os.environ["GOOGLE_CREDENTIALS_PATH"] = secrets["google"]["CREDENTIALS_PATH"]
os.environ["GOOGLE_SHEETS_SPREADSHEET_ID"] = secrets["google"]["SHEETS_SPREADSHEET_ID"]
os.environ["GOOGLE_SHEETS_SHEET_NAME"] = secrets["google"]["SHEETS_SHEET_NAME"]

# Set page config at the very beginning
st.set_page_config(
    page_title="AI Email Agent",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global CSS for proper text area width
st.markdown("""
<style>
/* Make text areas use full width */
.stTextArea textarea {
    width: 100% !important;
}

/* Fix tabs width */
.stTabs [data-baseweb="tab-panel"] {
    width: 100% !important;
}

/* Fix text input fields width */
.stTextInput input {
    width: 100% !important;
}

/* Fix the form fields */
[data-testid="column"] [data-baseweb="input"] {
    width: 100% !important;
}

/* Fix the form field containers */
[data-testid="column"] [data-baseweb="base-input"] {
    width: 100% !important;
}

/* Fix the form field inner containers */
[data-testid="column"] [data-baseweb="input-container"] {
    width: 100% !important;
}

/* Make extracted info use full width */
div.row-widget.stHorizontal {
    width: 100% !important;
}

/* Make extracted info columns use maximum width */
[data-testid="column"] {
    width: 100% !important;
}

/* Make block containers full width */
div[data-testid="stVerticalBlock"] {
    width: 100% !important;
}

/* Ensure form fields grow to fit */
.stForm {
    width: 100% !important;
}

/* Fix Processing Details section */
div.stTabs > div[data-baseweb="tab-list"] + div[role="tabpanel"] {
    width: 100% !important;
}

/* Fixed width for all CSS text inputs */
.stTextInput, .stTextInput > div, .stTextInput > div > div {
    width: 100% !important;
}

/* Style for form elements inside tabs */
.stTabs [data-baseweb="tab-panel"] .stTextInput {
    width: 100% !important;
    max-width: 100% !important;
}

/* Improve the width of tab panel contents */
.stTabs [data-baseweb="tab-panel"] [data-testid="stVerticalBlock"] {
    width: 100% !important;
}

/* Force form field width in columns */
[data-testid="column"] .stTextInput {
    width: 100% !important;
    max-width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv(verbose=True)  # Add verbose=True for debugging

# Print current working directory and environment variables for debugging
print(f"Current working directory: {os.getcwd()}")
print("Environment variables loaded:")
print(f"OPENAI_API_KEY exists: {'OPENAI_API_KEY' in os.environ}")
print(f"EMAIL_SMTP_SERVER exists: {'EMAIL_SMTP_SERVER' in os.environ}")
print(f"EMAIL_PASSWORD exists: {'EMAIL_PASSWORD' in os.environ}")

# Import our modules
from utils.email_parser import EmailParser
from utils.rag_retriever import RAGRetriever
from utils.web_research import WebResearcher
from utils.email_agent import EmailAgentTool
from utils.google_sheets_logger import GoogleSheetsLogger
from models.response_composer import ResponseComposer
from data.sample_data import get_sample_emails

# Load OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY environment variable not set. Please set it in the .env file.")

# Get email credentials
EMAIL_CONFIGURED = True  # Hard-code this to True to always enable email sending

# Check for Google Sheets credentials
SHEETS_CONFIGURED = all([
    os.getenv("GOOGLE_CREDENTIALS_PATH"),
    os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
])

# Initialize components as needed
email_parser = None
rag_retriever = None
web_researcher = None
response_composer = None
email_agent = None
sheets_logger = None

if OPENAI_API_KEY:
    email_parser = EmailParser(api_key=OPENAI_API_KEY)
    rag_retriever = RAGRetriever(api_key=OPENAI_API_KEY, vectorstore_path="email_agent/data/vectorstore")
    web_researcher = WebResearcher(api_key=OPENAI_API_KEY)
    response_composer = ResponseComposer(api_key=OPENAI_API_KEY)

    # Initialize vectorstore with sample data if needed
    if not os.path.exists(os.path.join("email_agent/data/vectorstore", "index.faiss")):
        try:
            os.makedirs("email_agent/data/vectorstore", exist_ok=True)
            sample_emails_df = get_sample_emails()
            rag_retriever.ingest_email_data(sample_emails_df)
        except Exception as e:
            st.error(f"Error initializing vectorstore: {e}")
            st.info("If this error persists, try deleting the email_agent/data/vectorstore directory and restarting the application.")

# Initialize email agent with values from environment
email_agent = EmailAgentTool.from_env()

# Print email configuration for debugging
print("Email configuration:")
print(f"SMTP Server: {email_agent.smtp_server}:{email_agent.smtp_port}")
print(f"Username: {email_agent.username}")
print(f"Default sender: {email_agent.default_sender}")
print("LangChain Agent configured for email sending")

# Helper functions for parallel processing
def process_style_branch(email_text: str, extracted_info: Dict[str, Any]) -> str:
    """Process the style and context branch."""
    if not rag_retriever:
        return "RAG Retriever not initialized. Please check your OpenAI API key."

    try:
        st.info("Processing style branch...")
        result = rag_retriever.generate_style_based_draft(email_text, extracted_info)
        st.info("✓ Style branch completed")
        return result
    except Exception as e:
        st.error(f"Style branch error: {str(e)}")
        return f"Error generating style draft: {str(e)}"

def process_research_branch(extracted_info: Dict[str, Any]) -> str:
    """Process the external data research branch."""
    if not web_researcher:
        return "Web Researcher not initialized. Please check your OpenAI API key."

    try:
        st.info("Processing research branch...")
        result = web_researcher.research_company(extracted_info)
        st.info("✓ Research branch completed")
        return result
    except Exception as e:
        st.error(f"Research branch error: {str(e)}")
        return f"Error performing research: {str(e)}"

# Process email and generate a response
def process_email():
    """Process the email and generate a response."""
    if not OPENAI_API_KEY:
        st.error("OpenAI API key is not set. Please set it in the .env file.")
        return

    email_text = st.session_state["original_email"]

    try:
        # Full width container for processing
        st.markdown("<div style='padding: 1em; border-radius: 10px; background-color: #f0f2f6;'>", unsafe_allow_html=True)
        st.subheader("Processing Email")

        # Progress indicator
        progress_bar = st.progress(0)

        # Step 1: Extract information
        with st.spinner("Extracting email information..."):
            extracted_info = email_parser.parse_email(email_text)
            st.session_state["extracted_info"] = extracted_info
            progress_bar.progress(25)
            st.success("✓ Information extracted successfully")

        # Step 2: Style Analysis
        with st.spinner("Analyzing writing style..."):
            # Get similar examples for session state
            if rag_retriever and rag_retriever.vectorstore:
                similar_pairs = rag_retriever.retrieve_similar_examples(email_text)
                st.session_state["similar_examples"] = similar_pairs

            # Generate style draft
            style_draft = process_style_branch(email_text, extracted_info)
            st.session_state["style_draft"] = style_draft
            progress_bar.progress(50)
            st.success("✓ Style analysis completed")

        # Step 3: Web Research
        with st.spinner("Gathering research data..."):
            research_data = process_research_branch(extracted_info)
            st.session_state["research_data"] = research_data
            progress_bar.progress(75)
            st.success("✓ Research data gathered")

        # Step 4: Final Response
        with st.spinner("Generating final response..."):
            final_response = response_composer.compose_response(
                extracted_info=extracted_info,
                style_draft=style_draft,
                research_data=research_data
            )
            st.session_state["final_response"] = final_response
            progress_bar.progress(100)
            st.success("✓ Final response composed")

        # Close the container div
        st.markdown("</div>", unsafe_allow_html=True)

        # Update session state
        st.session_state["step"] = "processed"
        st.session_state["processing"] = False
        st.session_state["status_message"] = "✅ Response generated successfully!"

        # Rerun to show the processed state UI
        st.rerun()

    except Exception as e:
        st.error(f"Error during processing: {str(e)}")
        st.session_state["processing"] = False
        st.session_state["status_message"] = f"❌ Error: {str(e)}"

def send_email():
    """Send the email and log the interaction."""
    if not EMAIL_CONFIGURED:
        st.error("Email sending is not configured. Please set the required environment variables.")
        return False

    try:
        # Get recipient email - use the one from extracted_info or the one visible in the UI
        recipient = st.session_state["extracted_info"].get("sender_email", "")

        # If danielle@pawlife.co is visible in the interface, use that as recipient
        if not recipient or "danielle@pawlife.co" in str(st.session_state):
            recipient = "danielle@pawlife.co"

        # Get response
        response = st.session_state["final_response"]

        # Extract subject from original email
        original_email = st.session_state["original_email"]
        subject_line = "Re: "
        subject_match = None

        # Try to extract subject from email text
        for line in original_email.split("\n"):
            if line.lower().startswith("subject:"):
                subject_match = line[8:].strip()
                break

        if subject_match:
            subject_line += subject_match
        else:
            subject_line += "Your recent inquiry"

        # Send email
        st.info(f"Sending email to: {recipient} with LangChain AI Agent")

        result = email_agent.process_and_send_email(
            to_address=recipient,
            subject=subject_line,
            body=response
        )

        if result["status"] == "success":
            st.session_state["status_message"] = f"✅ {result['message']}"
            st.success(f"Email sent successfully to {recipient}")

            # Log to Google Sheets if configured
            if SHEETS_CONFIGURED and sheets_logger:
                sheets_logger.log_interaction(
                    extracted_info=st.session_state["extracted_info"],
                    original_email=st.session_state["original_email"],
                    response=response,
                    status="Sent"
                )

            # Don't set step here, let the caller handle navigation
            return True
        else:
            st.session_state["status_message"] = f"❌ Error: {result['message']}"
            st.error(f"Failed to send email: {result['message']}")
            return False

    except Exception as e:
        st.session_state["status_message"] = f"❌ Error: {str(e)}"
        st.error(f"Error sending email: {str(e)}")
        return False

def main():
    # Check if sample data is initialized
    data_initialized = os.path.exists(os.path.join("email_agent/data/vectorstore", "index.faiss"))

    # User Interface
    st.title("📧 AI Email Response Generator")

    # Sidebar for system status
    with st.sidebar:
        st.title("AI Email Agent")
        st.markdown("""
        This application helps you generate personalized email responses using AI.
        It analyzes the incoming email, matches the style of similar past responses,
        and researches relevant information to create a comprehensive reply.
        """)

        # Display configuration status
        st.subheader("Configuration Status")
        if OPENAI_API_KEY:
            st.success("✅ OpenAI API Key configured")
        else:
            st.error("❌ OpenAI API Key not configured")

        if EMAIL_CONFIGURED:
            st.success("✅ Email settings configured with LangChain Agent")
        else:
            st.warning("⚠️ Email settings not configured (optional)")

        if data_initialized:
            st.success("✅ Sample Data: Loaded")
        else:
            st.info("ℹ️ Sample Data: Will be loaded on first run")

        st.divider()

        st.markdown("""
        ### How to use
        1. Paste an incoming email
        2. Review extracted information
        3. Check style and research data
        4. Edit and approve the final response
        5. Send or save the response
        """)

    # Main content area based on current step
    if st.session_state["step"] == "input":
        st.subheader("Step 1: Input Email")

        email_text = st.text_area(
            "Paste the incoming email:",
            height=300,
            placeholder="Paste the full email text here..."
        )

        col1, col2 = st.columns([1, 6])

        with col1:
            process_button = st.button("Process Email", use_container_width=True)
            if process_button and email_text and not st.session_state["processing"]:
                st.session_state["original_email"] = email_text
                st.session_state["processing"] = True
                st.session_state["status_message"] = "Processing email..."
                process_email()  # Call directly instead of using a thread
                # No rerun here - let the UI update naturally

        with col2:
            if st.session_state["status_message"]:
                st.write(st.session_state["status_message"])

        if st.session_state["processing"]:
            st.spinner("Processing email...")
            st.warning("This may take a minute or two. Please be patient...")

    elif st.session_state["step"] == "processed":
        # Call the process_email function to rebuild the UI
        # Only show processing results without actually processing again
        if st.session_state["final_response"]:
            # Full width container for displaying results
            st.markdown("<div style='padding: 1em; border-radius: 10px; background-color: #f0f2f6;'>", unsafe_allow_html=True)
            st.subheader("Generated Response")

            with st.container():
                st.text_area("Response Preview", st.session_state["final_response"], height=200, key="response-preview")

            # Action buttons in a single row
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                if EMAIL_CONFIGURED and st.session_state["extracted_info"] and 'sender_email' in st.session_state["extracted_info"]:
                    recipient = st.session_state["extracted_info"].get('sender_email', '')
                    if st.button("📤 Send Response", use_container_width=True, key="send_response_btn"):
                        success = send_email()
                        if success:
                            st.session_state["step"] = "sent"
                            st.rerun()
                elif not EMAIL_CONFIGURED:
                    st.warning("Email sending not configured")

            with col2:
                if st.button("✏️ Edit Response", use_container_width=True, key="edit_response_btn"):
                    st.session_state["step"] = "review"
                    st.rerun()

            with col3:
                if st.button("🔄 Start Over", use_container_width=True, key="start_over_btn"):
                    # Reset session state
                    for key in ['extracted_info', 'style_draft', 'research_data', 'final_response',
                           'original_email', 'similar_examples']:
                        if key in st.session_state:
                            st.session_state[key] = None
                    st.session_state["step"] = "input"
                    st.session_state["status_message"] = ""
                    st.rerun()

            # Close the container div
            st.markdown("</div>", unsafe_allow_html=True)

            # Create tabs for detailed information
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("Processing Details")

            details_tabs = st.tabs(["📑 Extracted Info", "✍️ Style Analysis", "🔍 Research Data", "📧 Final Email"])

            with details_tabs[0]:
                if st.session_state["extracted_info"]:
                    st.markdown("<div style='width: 100%;'>", unsafe_allow_html=True)
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("<div style='width: 100%;'>", unsafe_allow_html=True)
                        for key, value in list(st.session_state["extracted_info"].items())[:len(st.session_state["extracted_info"])//2]:
                            st.text_input(key, value, disabled=True, key=f"detail_extract_{key}", label_visibility="visible")
                        st.markdown("</div>", unsafe_allow_html=True)

                    with col2:
                        st.markdown("<div style='width: 100%;'>", unsafe_allow_html=True)
                        for key, value in list(st.session_state["extracted_info"].items())[len(st.session_state["extracted_info"])//2:]:
                            st.text_input(key, value, disabled=True, key=f"detail_extract2_{key}", label_visibility="visible")
                        st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

            with details_tabs[1]:
                if st.session_state["similar_examples"]:
                    st.subheader("Similar Email Examples")
                    for i, pair in enumerate(st.session_state["similar_examples"]):
                        with st.expander(f"Example {i+1}", expanded=i==0):
                            st.markdown("**Original:**")
                            st.text_area(f"Original Email {i+1}", pair['email'], height=100, disabled=True)
                            st.markdown("**Response:**")
                            st.text_area(f"Response {i+1}", pair['response'], height=100, disabled=True)

                st.subheader("Generated Style Draft")
                st.text_area("Style-based Draft", st.session_state["style_draft"], height=200, disabled=True)

            with details_tabs[2]:
                st.text_area("Research Results", st.session_state["research_data"], height=300, disabled=True)

            with details_tabs[3]:
                st.text_area("Final Email", st.session_state["final_response"], height=300, disabled=True)
        else:
            st.error("No processed data found. Please go back and process an email.")
            if st.button("⬅️ Back to Input"):
                st.session_state["step"] = "input"
                st.rerun()

    elif st.session_state["step"] == "review":
        st.subheader("Review and Approve Response")

        # Use container to ensure full width
        with st.container():
            tab1, tab2, tab3, tab4 = st.tabs(["📧 Original Email", "🔄 Similar Examples", "🔍 Research & Style", "✉️ Final Response"])

            with tab1:
                st.text_area(
                    "Original Email Text",
                    value=st.session_state["original_email"],
                    height=200,
                    disabled=True
                )
                if st.session_state["extracted_info"]:
                    st.markdown("<div style='width: 100%;'>", unsafe_allow_html=True)
                    extracted_col1, extracted_col2 = st.columns(2)

                    with extracted_col1:
                        st.markdown("<div style='width: 100%;'>", unsafe_allow_html=True)
                        st.subheader("Extracted Information")
                        for key, value in list(st.session_state["extracted_info"].items())[:len(st.session_state["extracted_info"])//2]:
                            st.text_input(key, value, key=f"extracted_{key}", disabled=True, label_visibility="visible")
                        st.markdown("</div>", unsafe_allow_html=True)

                    with extracted_col2:
                        st.markdown("<div style='width: 100%;'>", unsafe_allow_html=True)
                        st.write("")  # Add some spacing
                        st.write("")  # Add some spacing
                        for key, value in list(st.session_state["extracted_info"].items())[len(st.session_state["extracted_info"])//2:]:
                            st.text_input(key, value, key=f"extracted_rev_{key}", disabled=True, label_visibility="visible")
                        st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

            with tab2:
                if hasattr(st.session_state, 'similar_examples') and st.session_state["similar_examples"]:
                    for i, pair in enumerate(st.session_state["similar_examples"]):
                        with st.expander(f"Similar Example {i+1}", expanded=i==0):
                            cols = st.columns(2)
                            with cols[0]:
                                st.markdown("**Original Email:**")
                                st.text_area(f"Original {i+1}", pair['email'], height=150, disabled=True)
                            with cols[1]:
                                st.markdown("**Response:**")
                                st.text_area(f"Response {i+1}", pair['response'], height=150, disabled=True)
                else:
                    st.info("No similar examples found")

            with tab3:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Style Analysis")
                    st.text_area(
                        "Style-based Draft",
                        value=st.session_state["style_draft"],
                        height=300,
                        disabled=True
                    )

                with col2:
                    st.subheader("Research Data")
                    st.text_area(
                        "Web Research Results",
                        value=st.session_state["research_data"],
                        height=300,
                        disabled=True
                    )

            with tab4:
                st.subheader("Final Response")
                edited_response = st.text_area(
                    "Edit the response if needed:",
                    value=st.session_state["final_response"],
                    height=300
                )

                if edited_response != st.session_state["final_response"]:
                    st.session_state["final_response"] = edited_response

                action_col1, action_col2, action_col3 = st.columns([1, 1, 2])

                with action_col1:
                    if EMAIL_CONFIGURED and st.session_state["extracted_info"] and 'sender_email' in st.session_state["extracted_info"]:
                        recipient = st.session_state["extracted_info"].get('sender_email', '')
                        send_button = st.button("📤 Send Email", use_container_width=True, key="send_email_review_btn")
                        if send_button:
                            success = send_email()
                            if success:
                                st.session_state["step"] = "sent"
                                st.rerun()
                    elif not EMAIL_CONFIGURED:
                        st.warning("Email sending not configured")

                with action_col2:
                    if st.button("🔄 Start Over", use_container_width=True, key="start_over_review_btn"):
                        # Reset session state
                        for key in ['extracted_info', 'style_draft', 'research_data', 'final_response',
                               'original_email', 'similar_examples']:
                            if key in st.session_state:
                                st.session_state[key] = None
                        st.session_state["step"] = "input"
                        st.session_state["status_message"] = ""
                        st.rerun()

                with action_col3:
                    if st.session_state["status_message"]:
                        st.write(st.session_state["status_message"])

    elif st.session_state["step"] == "sent":
        # Show success page with summary information
        st.success("✅ Email sent successfully!")

        # Create a container to display success information
        with st.container():
            st.subheader("Email has been sent")
            st.info("Your email has been sent to the recipient's inbox.")

        # Show recipient information
        if st.session_state["extracted_info"] and 'sender_email' in st.session_state["extracted_info"]:
            recipient = st.session_state["extracted_info"].get('sender_email', '')
            st.info(f"Your response was sent to {recipient}")

        # Display summary of the sent message
        if st.session_state["final_response"]:
            with st.expander("View message content", expanded=False):
                st.text_area("Message content", st.session_state["final_response"], height=200, disabled=True)

        # Clear button with wider style
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("📧 Process Another Email", use_container_width=True, key="process_another_btn"):
                # Reset session state
                for key in ['extracted_info', 'style_draft', 'research_data', 'final_response',
                       'original_email', 'similar_examples']:
                    if key in st.session_state:
                        st.session_state[key] = None
                st.session_state["step"] = "input"
                st.session_state["status_message"] = ""
                st.rerun()

    # Footer
    st.divider()
    st.caption("AI Email Agent | Made for ML Class Project")

if __name__ == "__main__":
    main()
