import os
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1CFhX3QeKAuHUquXWPaapXIwlK1k8i5PNW3VCDSi7MzU"
SHEET_GID = 1988614547

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_sheet():
    creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
    creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    # Find the worksheet by gid
    for ws in spreadsheet.worksheets():
        if ws.id == SHEET_GID:
            return ws
    raise ValueError(f"No worksheet found with gid {SHEET_GID}")


def append_candidate(extracted: dict, intent: str, sender: str):
    """Append a row to the subletter/roommate tracking sheet.

    Columns: Person | Contact | Notes | Next step | Interviewers | Interview notes
    """
    sheet = _get_sheet()

    name = extracted.get("name") or ""
    # Build contact from phone, socials, and sender
    contact_parts = []
    if extracted.get("phone"):
        contact_parts.append(extracted["phone"])
    if extracted.get("socials"):
        contact_parts.append(extracted["socials"])
    if not contact_parts:
        # Fall back to WhatsApp sender number
        contact_parts.append(sender.replace("whatsapp:", ""))
    contact = ", ".join(contact_parts)

    notes = extracted.get("notes") or ""
    if extracted.get("start_date") or extracted.get("end_date"):
        dates = f"{extracted.get('start_date', '?')} → {extracted.get('end_date', '?')}"
        notes = f"{dates}. {notes}" if notes else dates

    next_step = "New — needs interview"
    interviewers = ""
    interview_notes = ""

    row = [name, contact, notes, next_step, interviewers, interview_notes]
    sheet.insert_row(row, index=2, value_input_option="USER_ENTERED")
    print(f"  → inserted to Google Sheet (row 2): {row}")
