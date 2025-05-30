from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from email.mime.text import MIMEText
from dotenv import load_dotenv
import smtplib
import requests
import json
import os
import time
import re
import pandas as pd
import io
import dateutil.parser
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Config
API_KEY = os.getenv("BLAND_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-2.0-flash")
headers = {'Authorization': f'Bearer {API_KEY}'}

# FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Scheduler
scheduler = BackgroundScheduler(executors={'default': ThreadPoolExecutor(10)})
scheduler.start()

# Utility functions
def extract_json_from_response(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            return {}
    return {}

def analyze_transcript(transcript):
    prompt = f"""
You are an AI assistant analyzing a customer support call transcript from a bank. Here is the transcript:

\"\"\"{transcript}\"\"\"

Provide:
1. Summary of the call.
2. Any mentioned repayment date.
3. Issues raised by customer.
4. Did customer ask about amount due? If yes, what did bot reply?
5. Sentiment details.

JSON only:
{{
  "summary": "...",
  "repayment_date": "...",
  "issues": "...",
  "amount_due_discussion": {{
    "customer_question": "...",
    "bot_response": "..."
  }},
  "sentiment": {{
    "tone": "...",
    "topics_discussed": ["..."],
    "problems_raised": ["..."]
  }}
}}
"""
    try:
        res = gemini.generate_content(prompt)
        return extract_json_from_response(res.text)
    except:
        return {}

def send_reminder_email(summary, repayment_date):
    subject = "📬 Loan Repayment Reminder"
    body = f"Hi,\n\nThis is a reminder regarding your scheduled repayment.\n\nSummary from the call:\n{summary}\n\nRepayment Date: {repayment_date}\n\nThank you,\nAindriya Bank"
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = EMAIL_RECIPIENT

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, EMAIL_RECIPIENT, msg.as_string())
        print("✅ Reminder email sent to", EMAIL_RECIPIENT)
    except Exception as e:
        print("Email failed:", e)

def normalize_phone(phone: str):
    phone = str(phone).strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone

def initiate_call(name: str, phone: str):
    phone = normalize_phone(phone)
    call_data = {
        "phone_number": phone,
        "voice": "June",
        "wait_for_greeting": False,
        "record": True,
        "answered_by_enabled": True,
        "noise_cancellation": False,
        "interruption_threshold": 100,
        "block_interruptions": False,
        "max_duration": 12,
        "model": "base",
        "language": "en",
        "background_track": "office",
        "voicemail_action": "hangup",
        "task": """We're reaching out to remind you that your recent loan payment is currently overdue.
                    We’d like to confirm when you will be able to make the repayment. 
                    If you mention something like "today", "tomorrow", or "next week", 
                    please also confirm the actual date (e.g., May 31st or June 2nd) so we can schedule your reminder accurately.
                    Could you please let us know your intended payment date, or if you’re facing any issues we should be aware of?""",
        "first_sentence": f"Hello, this is Aindriya Bank calling. Am I speaking with {name}?"
    }

    response = requests.post('https://api.bland.ai/v1/calls', json=call_data, headers=headers)
    call_response = response.json()
    return call_response.get("call_id")

# Routes
@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/start-call/")
async def start_call(data: dict):
    name = data.get("name")
    phone = normalize_phone(data.get("phone"))
    call_id = initiate_call(name, phone)
    if call_id:
        return {"message": f"Initiated call to {name}", "call_id": call_id}
    return {"error": "Call initiation failed"}

@app.get("/call-status/{call_id}")
async def check_call_status(call_id: str):
    try:
        status = requests.get(f"https://api.bland.ai/v1/calls/{call_id}", headers=headers)
        if status.status_code == 200:
            details = status.json()
            current_status = details.get("status")
            if current_status == "completed":
                transcript = details.get("concatenated_transcript", "")
                gemini_results = analyze_transcript(transcript)
                repayment_raw = gemini_results.get("repayment_date")
                if repayment_raw:
                    try:
                        dt = dateutil.parser.parse(repayment_raw, fuzzy=True).replace(hour=9, minute=0)
                        print(f"📅 Parsed repayment date: {dt}")
                        scheduler.add_job(send_reminder_email, 'date', run_date=dt, args=[gemini_results["summary"], repayment_raw])
                        print(f"📧 Email scheduled for: {dt}")
                    except:
                        pass
                return {"status": "completed"}
            elif current_status in ["failed", "no_answered"]:
                return {"status": "rejected"}
            else:
                return {"status": "initiating"}
        else:
            return {"status": "error"}
    except:
        return {"status": "error"}

@app.post("/upload-contacts/")
async def upload_contacts(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        filename = file.filename.lower()
        if filename.endswith(".csv"):
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            return {"error": "Unsupported file format"}

        results = []
        for _, row in df.iterrows():
            name = str(row.get("name", "")).strip()
            phone = normalize_phone(str(row.get("phone", "")).strip())
            if not name or not phone:
                continue
            call_id = initiate_call(name, phone)
            results.append({
                "name": name,
                "phone": phone,
                "status": "initiating" if call_id else "error",
                "call_id": call_id
            })
            time.sleep(2)  # avoid rate limiting

        return {"message": "Bulk calls initiated", "results": results}
    except Exception as e:
        return {"error": f"Failed to process file: {e}"}
