import os
import json
from typing import Dict, Any, List, Optional
import datetime
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account

class GoogleSheetsLogger:
    """
    Utility for logging email interactions to Google Sheets.
    """

    def __init__(self,
                credentials_path: str,
                spreadsheet_id: str,
                sheet_name: str = "Email Interactions"):
        """
        Initialize the Google Sheets logger.

        Args:
            credentials_path: Path to service account credentials JSON file
            spreadsheet_id: ID of the Google Sheets spreadsheet
            sheet_name: Name of the sheet to write to
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.service = None

        # Initialize Google Sheets API service
        self._initialize_service()

        # Ensure the sheet exists and has the correct headers
        self._initialize_sheet()

    def _initialize_service(self) -> None:
        """Initialize the Google Sheets API service."""
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path, scopes=SCOPES)
            self.service = build('sheets', 'v4', credentials=credentials)
        except Exception as e:
            print(f"Error initializing Google Sheets service: {e}")
            self.service = None

    def _initialize_sheet(self) -> None:
        """Ensure the sheet exists and has the correct headers."""
        if not self.service:
            return

        try:
            # Check if sheet exists
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id).execute()

            sheets = sheet_metadata.get('sheets', [])
            sheet_exists = False

            for sheet in sheets:
                if sheet['properties']['title'] == self.sheet_name:
                    sheet_exists = True
                    break

            # Create sheet if it doesn't exist
            if not sheet_exists:
                request = {
                    "requests": [{
                        "addSheet": {
                            "properties": {
                                "title": self.sheet_name
                            }
                        }
                    }]
                }
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=request
                ).execute()

            # Add headers if sheet is empty
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A1:Z1"
            ).execute()

            if 'values' not in result:
                headers = [
                    "Timestamp",
                    "Sender Name",
                    "Sender Email",
                    "Company Name",
                    "Industry",
                    "Funding Stage",
                    "Ask Amount",
                    "Request Summary",
                    "Key Points",
                    "Original Email",
                    "Response",
                    "Status"
                ]

                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self.sheet_name}!A1",
                    valueInputOption="RAW",
                    body={"values": [headers]}
                ).execute()

        except Exception as e:
            print(f"Error initializing sheet: {e}")

    def log_interaction(self,
                       extracted_info: Dict[str, Any],
                       original_email: str,
                       response: str,
                       status: str = "Sent") -> bool:
        """
        Log an email interaction to Google Sheets.

        Args:
            extracted_info: Dictionary of extracted entities from email
            original_email: Original email text
            response: Response email text
            status: Status of the interaction (e.g., "Sent", "Draft", "Error")

        Returns:
            Boolean indicating success
        """
        if not self.service:
            return False

        try:
            # Prepare row data
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            row = [
                timestamp,
                extracted_info.get("sender_name", ""),
                extracted_info.get("sender_email", ""),
                extracted_info.get("company_name", ""),
                extracted_info.get("industry", ""),
                extracted_info.get("funding_stage", ""),
                extracted_info.get("ask_amount", ""),
                extracted_info.get("request_summary", ""),
                str(extracted_info.get("key_points", "")),
                original_email,
                response,
                status
            ]

            # Append to sheet
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A1",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [row]}
            ).execute()

            return True

        except Exception as e:
            print(f"Error logging to Google Sheets: {e}")
            return False

    def get_historical_data(self, limit: int = 100) -> pd.DataFrame:
        """
        Retrieve historical email interactions.

        Args:
            limit: Maximum number of rows to retrieve

        Returns:
            DataFrame of historical interactions
        """
        if not self.service:
            return pd.DataFrame()

        try:
            # Get sheet data
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A1:Z{limit+1}"
            ).execute()

            values = result.get('values', [])

            if not values or len(values) <= 1:  # Only headers or empty
                return pd.DataFrame()

            # Convert to DataFrame
            headers = values[0]
            data = values[1:limit+1]

            # Ensure all rows have the same length as headers
            for i in range(len(data)):
                while len(data[i]) < len(headers):
                    data[i].append("")

            df = pd.DataFrame(data, columns=headers)
            return df

        except Exception as e:
            print(f"Error retrieving historical data: {e}")
            return pd.DataFrame()

    @classmethod
    def from_env(cls):
        """
        Create a GoogleSheetsLogger from environment variables.

        Environment variables needed:
        - GOOGLE_CREDENTIALS_PATH
        - GOOGLE_SHEETS_SPREADSHEET_ID
        - GOOGLE_SHEETS_SHEET_NAME (optional)

        Returns:
            GoogleSheetsLogger instance
        """
        credentials_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
        spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID")
        sheet_name = os.environ.get("GOOGLE_SHEETS_SHEET_NAME", "Email Interactions")

        if not all([credentials_path, spreadsheet_id]):
            raise ValueError("Missing required environment variables for Google Sheets logging")

        return cls(
            credentials_path=credentials_path,
            spreadsheet_id=spreadsheet_id,
            sheet_name=sheet_name
        )
