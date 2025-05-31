from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from dotenv import load_dotenv
from datetime import datetime
import io
import pandas as pd
import time
from app.models import CallRequest
from app.utils import normalize_phone
from app.services.bland import initiate_call, check_bland_call_status
from app.services.gemini import analyze_transcript
from app.services.emailer import send_reminder_email

# Load .env
load_dotenv()

# FastAPI setup
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

# APScheduler
scheduler = BackgroundScheduler(executors={'default': ThreadPoolExecutor(10)})
scheduler.start()

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/start-call/")
async def start_call(data: CallRequest):
    call_id = initiate_call(data.name, normalize_phone(data.phone), data.due_amount, data.due_date)
    if call_id:
        return {"message": f"Initiated call to {data.name}", "call_id": call_id}
    return {"error": "Call initiation failed"}

@app.get("/call-status/{call_id}")
async def call_status(call_id: str):
    status, transcript = check_bland_call_status(call_id)
    if status == "completed" and transcript:
        gemini_data = analyze_transcript(transcript)
        repayment_raw = gemini_data.get("repayment_date")
        if repayment_raw:
            try:
                from dateutil import parser
                dt = parser.parse(repayment_raw, fuzzy=True).replace(hour=9, minute=0)
                if dt > datetime.now():
                    scheduler.add_job(send_reminder_email, 'date', run_date=dt, args=[gemini_data["summary"], repayment_raw])
            except Exception as e:
                print("❌ Date parse error:", e)
    return {"status": status}

@app.post("/upload-contacts/")
async def upload_contacts(file: UploadFile = File(...)):
    contents = await file.read()
    filename = file.filename.lower()
    if filename.endswith(".csv"):
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(contents))
    else:
        return {"error": "Unsupported file format"}

    results = []
    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        phone = normalize_phone(str(row.get("phone", "")).strip())
        due_amount = str(row.get("due_amount", "")).strip()
        due_date = str(row.get("due_date", "")).strip()
        if not name or not phone or not due_amount or not due_date:
            continue
        call_id = initiate_call(name, phone, due_amount, due_date)
        results.append({
            "name": name,
            "phone": phone,
            "status": "initiating" if call_id else "error",
            "call_id": call_id
        })
        time.sleep(2)

    return {"message": "Bulk calls initiated", "results": results}
