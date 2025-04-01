"""
Email Agent - An AI-powered email response generation system.
"""

from .utils import EmailParser, RAGRetriever, WebResearcher, GoogleSheetsLogger
from .models.response_composer import ResponseComposer
from .data.sample_data import get_sample_emails

__all__ = [
    'EmailParser',
    'RAGRetriever',
    'WebResearcher',
    'GoogleSheetsLogger',
    'ResponseComposer',
    'get_sample_emails',
]
