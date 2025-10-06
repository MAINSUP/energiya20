import gspread
import pandas as pd
from sqlalchemy import create_engine
from lead_scoring import score_lead
from oauth2client.service_account import ServiceAccountCredentials
import logging

# -------------------------
# Logging
# -------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# -------------------------
# Google Sheets setup
# -------------------------
SHEET_NAME = "Energiya2.0_conversion"
SERVICE_ACCOUNT_PATH = "/locales/service_account.json"

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_PATH, scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# -------------------------
# SQL Setup (MySQL example)
# -------------------------
# Example: mysql+pymysql://username:password@localhost:3306/leads_db
engine = create_engine("mysql+pymysql://username:password@localhost:3306/leads_db")

# -------------------------
# Sync function
# -------------------------
def sync_sheets_to_sql():
    try:
        data = sheet.get_all_records()
        if not data:
            logger.warning("No data found in Google Sheets.")
            return

        df = pd.DataFrame(data)

        # Compute lead score
        df["Score"] = df.apply(lambda row: score_lead(row.to_dict()), axis=1)

        # Write to SQL (replace table)
        df.to_sql("leads", engine, if_exists="replace", index=False)
        logger.info("✅ Google Sheets synced to SQL successfully.")

    except Exception as e:
        logger.exception(f"Error syncing Google Sheets to SQL: {e}")

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    sync_sheets_to_sql()
