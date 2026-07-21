"""
Google Sheets storage layer. Writes one row per lead, incrementally, so
a mid-run crash doesn't lose already-processed leads.
"""
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from config import settings
from logger import get_logger

log = get_logger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

HEADER = [
    "name",
    "address",
    "phone",
    "website",
    "email",
    "rating",
    "status",
    "notes",
    "timestamp",
]


class SheetStorage:
    def __init__(self, worksheet_title: str = "leads"):
        creds = Credentials.from_service_account_file(
            settings.google_sheets_credentials_path, scopes=SCOPES
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(settings.google_sheet_id)

        try:
            self.worksheet = spreadsheet.worksheet(worksheet_title)
        except gspread.WorksheetNotFound:
            self.worksheet = spreadsheet.add_worksheet(
                title=worksheet_title, rows=1000, cols=len(HEADER)
            )

        self._ensure_header()

    def _ensure_header(self) -> None:
        first_row = self.worksheet.row_values(1)
        if first_row != HEADER:
            self.worksheet.update("A1", [HEADER])

    def append_lead(
        self,
        name: str,
        address: str,
        phone: Optional[str],
        website: Optional[str],
        email: Optional[str],
        rating: Optional[float],
        status: str,
        notes: str,
        timestamp: str,
    ) -> None:
        row = [
            name,
            address or "",
            phone or "",
            website or "",
            email or "",
            rating if rating is not None else "",
            status,
            notes,
            timestamp,
        ]
        try:
            self.worksheet.append_row(row, value_input_option="USER_ENTERED")
        except gspread.exceptions.APIError as exc:
            log.error("Failed to write row for %s: %s", name, exc)
