from fastapi import FastAPI
from pydantic import BaseModel
from export_to_gsheet import append_lead
from lead_scoring import score_lead
import requests
import logging
import os
from fastapi.responses import JSONResponse

# --- Logging setup ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "fast_api.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

app = FastAPI()

class Lead(BaseModel):
    name: str
    email: str
    phone: str
    service_type: str
    kWt: str = ""
    status: str = "RFQ"

ENABLE_TELEGRAM = os.getenv("ENABLE_TELEGRAM", "false").lower() == "true"

def notify_telegram(lead):
    text = f"New Lead:\nName: {lead['name']}\nEmail: {lead['email']}\nPhone: {lead['phone']}\nService: {lead['service_type']}\nScore: {score_lead(lead)}"
    url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
    requests.post(url, data={"chat_id": os.getenv("TELEGRAM_CHAT_ID"), "text": text})

@app.post("/lead")
def receive_lead(lead: Lead):
    lead_dict = lead.dict()
    logger.info(f"Received new lead: {lead_dict}")

    try:
        score = score_lead(lead_dict)
        logger.info(f"Lead score: {score}")
        append_lead(lead_dict)
        logger.info("Lead successfully appended to Google Sheets")

        if ENABLE_TELEGRAM:
            notify_telegram(lead_dict)

        return JSONResponse(content={"message": "Lead saved", "score": score}, status_code=201)

    except Exception as e:
        logger.exception("Error processing lead")
        return JSONResponse(content={"error": str(e)}, status_code=500)
