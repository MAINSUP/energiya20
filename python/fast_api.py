from fastapi import FastAPI
from pydantic import BaseModel
from export_to_gsheet import append_lead
from lead_scoring import score_lead
import requests

app = FastAPI()

class Lead(BaseModel):
    name: str
    email: str
    phone: str
    service_type: str
    kWt: str = ""
    status: str = "RFQ"

TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

def notify_telegram(lead):
    text = f"New Lead:\nName: {lead['name']}\nEmail: {lead['email']}\nPhone: {lead['phone']}\nService: {lead['service_type']}\nScore: {score_lead(lead)}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})

@app.post("/lead")
def receive_lead(lead: Lead):
    lead_dict = lead.dict()
    append_lead(lead_dict)        # save to Google Sheets
    notify_telegram(lead_dict)   # send Telegram notification
    return {"message":"Lead saved", "score": score_lead(lead_dict)}
