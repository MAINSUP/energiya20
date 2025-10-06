# app.py
import os
import pandas as pd
import requests
import gspread
from functools import wraps
from flask import Flask, session, redirect, url_for, request, jsonify, render_template
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from functools import lru_cache
import time
import logging
from logging.handlers import RotatingFileHandler
import os

# --- Logging setup ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, "app.log")

handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=5)
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)

load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
app.config.update(
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE","True") == "True",
    SESSION_COOKIE_HTTPONLY = True,
    SESSION_COOKIE_SAMESITE = "Lax",
)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

# OAuth setup
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params={'access_type': 'offline'},
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
)

# Config: allowed admin emails or domain
ADMIN_EMAILS = set([e.strip().lower() for e in os.environ.get("ADMIN_EMAILS","").split(",") if e.strip()])
ADMIN_DOMAIN = os.environ.get("ADMIN_DOMAIN", "").lower().strip()  # e.g., "yourcompany.com"

# Google Sheets authentication
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/locales/service_account.json", scope)
client = gspread.authorize(creds)

sheet = client.open("Energiya2.0_conversion").sheet1


def load_leads_from_sheet():
    """Load leads from Google Sheets via gspread and return normalized dicts."""
    app.logger.info("Loading leads from Google Sheet...")

    if not sheet:
        app.logger.error("Google Sheet client not initialized.")
        return []

    try:
        data = sheet.get_all_records()
    except Exception as e:
        app.logger.exception(f"Failed to load data from sheet: {e}")
        return []

    app.logger.info(f"Retrieved {len(data)} rows from sheet.")

    if not data:
        return []

    leads = []
    skipped_rows = 0
    for i, row in enumerate(data, start=2):  # start=2 since row 1 is headers
        try:
            lat = float(str(row.get("lat", "")).strip()) if row.get("lat") else None
            lon = float(str(row.get("lon", "")).strip()) if row.get("lon") else None
        except ValueError:
            app.logger.warning(f"Invalid coordinates at row {i}: {row}")
            skipped_rows += 1
            continue

        if lat is None or lon is None:
            skipped_rows += 1
            continue

        leads.append({
            "name": (str(row.get("name") or "").strip()),
            "email": (str(row.get("email") or "").strip()),
            "phone": (str(row.get("phone") or "").strip()),
            "address": (str(row.get("address") or "").strip()),
            "property": (str(row.get("property") or "").strip()),
            "lat": lat,
            "lon": lon,
            "date": (str(row.get("date") or "").strip()),
            "status": (str(row.get("status") or "").strip()),
            "type": (str(row.get("type") or "").strip()),
            "kWt": (str(row.get("kWt") or "").strip()),
        })

    app.logger.info(f"Loaded {len(leads)} leads. Skipped {skipped_rows} invalid rows.")
    return leads


# --- Authorization check helper ---
def is_user_authorized(user):
    """Only allow authorized admin emails."""
    authorized_emails = {"yourname@company.com", "admin@company.com"}
    return user.get("email") in authorized_emails

# --- Login Required Decorator ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            app.logger.warning(f"Unauthorized access to {request.path}")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated

# --- Routes ---
@app.route("/")
def index():
    user = session.get("user")
    app.logger.info(f"User accessed index: {user}")
    return render_template("index.html", user=user)

@app.route("/login")
def login():
    redirect_uri = url_for("auth_callback", _external=True)
    app.logger.info("Redirecting user to Google login")
    return oauth.google.authorize_redirect(redirect_uri)

@app.route("/auth/callback")
def auth_callback():
    try:
        token = oauth.google.authorize_access_token()
        userinfo = oauth.google.parse_id_token(token)
        if not userinfo:
            userinfo = oauth.google.get("userinfo").json()

        app.logger.info(f"User logged in: {userinfo.get('email')}")

        session["user"] = {
            "email": userinfo.get("email"),
            "name": userinfo.get("name"),
            "picture": userinfo.get("picture"),
        }
        session["is_admin"] = is_user_authorized(session["user"])

        return redirect(url_for("index"))

    except Exception as e:
        app.logger.error(f"Login failed: {e}", exc_info=True)
        return "Authentication failed.", 500

@app.route("/logout")
def logout():
    user = session.pop("user", None)
    session.clear()
    app.logger.info(f"User logged out: {user}")
    return redirect(url_for("index"))


@lru_cache(maxsize=1)
def _cached_leads_data(_=None):
    return load_leads_from_sheet()

def get_leads_with_cache(ttl=300):
    """Cache leads for 5 minutes to avoid rate limits."""
    now = int(time.time())
    key = now // ttl
    return _cached_leads_data(key)


@app.route("/api/leads")
def api_leads():
    user = session.get('user', None)
    authorized = session.get('is_admin', False)

    app.logger.info(f"API /leads requested. User={user}, authorized={authorized}")

    leads = load_leads_from_sheet()
    hidden_statuses = {"rfq", "lost", "claim"}

    if not authorized:
        before = len(leads)
        leads = [l for l in leads if l.get("status", "").lower() not in hidden_statuses]
        for l in leads:
            l.pop("email", None)
            l.pop("phone", None)
            l.pop("address", None)
        app.logger.info(f"Filtered leads for unauthorized user: {before} → {len(leads)}")

    app.logger.info(f"Returning {len(leads)} leads to client.")
    return jsonify(leads)


# Example admin-only endpoint
@app.route("/admin/leads")
@login_required
def admin_leads():
    if not session.get('is_admin', False):
        return "Forbidden", 403
    leads = load_leads_from_sheet()
    return render_template("admin_leads.html", leads=leads, user=session.get('user'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
