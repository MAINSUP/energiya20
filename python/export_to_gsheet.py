# export_to_gsheet.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from lead_scoring import score_lead

# Google Sheets authentication
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/locales/service_account.json", scope)
client = gspread.authorize(creds)

sheet = client.open("Energiya2.0_conversion").sheet1

def append_lead(lead):
    lead_score = score_lead(lead)
    row = [
        lead.get("name",""),
        lead.get("email",""),
        lead.get("phone",""),
        lead.get("service_type",""),
        lead.get("kWt",""),
        lead.get("status","Pending"),
        lead_score
    ]
    sheet.append_row(row)
    print("Lead exported to Google Sheets with score:", lead_score)


