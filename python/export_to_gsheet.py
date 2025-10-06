import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from lead_scoring import score_lead

# ----------------------------------------------------------------------
# Logging setup
# ----------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# ----------------------------------------------------------------------
# Google Sheets setup
# ----------------------------------------------------------------------
SHEET_NAME = "Energiya2.0_conversion"
SERVICE_ACCOUNT_PATH = "/locales/service_account.json"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet():
    """Lazily connect to Google Sheets and return the sheet object."""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_PATH, scope)
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        return sheet
    except Exception as e:
        logger.error(f"Failed to connect to Google Sheets: {e}")
        return None

# ----------------------------------------------------------------------
# Append lead
# ----------------------------------------------------------------------
def append_lead(lead: dict):
    """
    Appends a new lead row to Google Sheets with computed score.
    """
    sheet = get_sheet()
    if sheet is None:
        logger.error("No Google Sheet connection available. Skipping lead append.")
        return False

    try:
        lead_score = score_lead(lead)
        row = [
            lead.get("name", ""),
            lead.get("email", ""),
            lead.get("phone", ""),
            lead.get("service_type", ""),
            lead.get("kWt", ""),
            lead.get("status", "Pending"),
            lead_score
        ]
        sheet.append_row(row)
        logger.info(f"✅ Lead exported to Google Sheets (score={lead_score})")
        return True
    except Exception as e:
        logger.exception(f"Error appending lead to sheet: {e}")
        return False
