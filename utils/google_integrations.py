import os
import json
import base64
import logging
import asyncio
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/spreadsheets",
]

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "google_token.json"


def get_google_service(service_name: str, version: str):
    """Authenticate and return a Google API service client."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build(service_name, version, credentials=creds)


# --------------------------------------------------------------------------
# GMAIL FUNCTIONS
# --------------------------------------------------------------------------

def fetch_important_emails(max_results: int = 5) -> List[Dict[str, Any]]:
    """Fetch latest important (unread) emails from Gmail inbox."""
    try:
        service = get_google_service("gmail", "v1")
        results = service.users().messages().list(
            userId="me", labelIds=["INBOX", "UNREAD"], maxResults=max_results
        ).execute()

        messages = results.get("messages", [])
        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId="me", id=msg["id"], format="full"
            ).execute()
            headers = {h["name"]: h["value"] for h in msg_data["payload"]["headers"]}
            snippet = msg_data.get("snippet", "")
            emails.append({
                "id": msg["id"],
                "from": headers.get("From", "Unknown"),
                "subject": headers.get("Subject", "(No Subject)"),
                "date": headers.get("Date", ""),
                "snippet": snippet[:300],
            })
        return emails
    except Exception as e:
        logger.error(f"Gmail fetch error: {e}")
        return []


def send_gmail_reply(message_id: str, reply_text: str, recipient: str, subject: str) -> bool:
    """Send a reply email via Gmail API."""
    try:
        service = get_google_service("gmail", "v1")
        message = MIMEText(reply_text)
        message["to"] = recipient
        message["subject"] = f"Re: {subject}"
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(
            userId="me", body={"raw": raw, "threadId": message_id}
        ).execute()
        return True
    except Exception as e:
        logger.error(f"Gmail send error: {e}")
        return False


# --------------------------------------------------------------------------
# GOOGLE CALENDAR FUNCTIONS
# --------------------------------------------------------------------------

def fetch_todays_events() -> List[Dict[str, Any]]:
    """Fetch today's Google Calendar events."""
    from datetime import datetime, timezone
    try:
        service = get_google_service("calendar", "v3")
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0).isoformat()
        end_of_day = now.replace(hour=23, minute=59, second=59).isoformat()

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = []
        for event in events_result.get("items", []):
            start = event["start"].get("dateTime", event["start"].get("date", ""))
            events.append({
                "id": event["id"],
                "summary": event.get("summary", "Untitled Event"),
                "start": start,
                "location": event.get("location", ""),
                "meet_link": event.get("hangoutLink", ""),
            })
        return events
    except Exception as e:
        logger.error(f"Calendar fetch error: {e}")
        return []


def create_calendar_event(summary: str, start_datetime: str, end_datetime: str, description: str = "") -> Optional[str]:
    """Create a Google Calendar event. Datetimes as ISO strings."""
    try:
        service = get_google_service("calendar", "v3")
        event_body = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"},
        }
        event = service.events().insert(calendarId="primary", body=event_body).execute()
        return event.get("htmlLink", "")
    except Exception as e:
        logger.error(f"Calendar create error: {e}")
        return None


# --------------------------------------------------------------------------
# GOOGLE SHEETS FUNCTIONS
# --------------------------------------------------------------------------

def log_expense_to_sheet(sheet_url: str, date: str, category: str, description: str, amount: str) -> bool:
    """Append an expense row to a Google Sheet."""
    try:
        import gspread
        from google.oauth2.credentials import Credentials

        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open_by_url(sheet_url)
        ws = sh.sheet1

        # Create header row if empty
        if ws.row_count == 0 or ws.cell(1, 1).value != "Date":
            ws.append_row(["Date", "Category", "Description", "Amount (₹)"])

        ws.append_row([date, category, description, amount])
        return True
    except Exception as e:
        logger.error(f"Google Sheets log error: {e}")
        return False
