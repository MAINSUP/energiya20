import gspread
import pandas as pd
from sqlalchemy import create_engine
from lead_scoring import score_lead


# Google Sheets Setup
creds = gspread.service_account(filename="service_account.json")
sheet = creds.open("Energiya2.0_conversion").sheet1

# SQL Setup (mySQL example)
engine = create_engine("mysql://username:password@localhost:5432/leads_db")


def sync_sheets_to_sql():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df["Score"] = df.apply(score_lead, axis=1)
    df.to_sql("leads", engine, if_exists="replace", index=False)
    print("Google Sheets synced to SQL successfully.")

if __name__ == "__main__":
    sync_sheets_to_sql()
