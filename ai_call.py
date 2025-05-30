import requests
import os
import json
import time
import re
from dotenv import load_dotenv
import google.generativeai as genai
from apscheduler.schedulers.background import BackgroundScheduler
from email.mime.text import MIMEText
import smtplib
import dateutil.parser

# Load environment variables
load_dotenv()

# Load Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Gemini model setup
gemini = genai.GenerativeModel("gemini-2.0-flash")

# Load email config
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

# Load Bland API key
API_KEY = os.getenv("BLAND_API_KEY")

headers = {
    'Authorization': f'Bearer {API_KEY}',
}

# Call data
call_data = {
    "phone_number": "+917871973103",
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
    Could you please let us know your intended payment date, or if you’re facing any issues we should be aware of?""",
    "first_sentence": "Hello, this is courtesy call from Aindriya Bank, regarding your outstanding loan balance."
}

# Start the call
response = requests.post('https://api.bland.ai/v1/calls', json=call_data, headers=headers)
call_response = response.json()
call_id = call_response.get("call_id")

if not call_id:
    print("❌ Call ID not found. Aborting.")
    exit()

print(f"✅ Call initiated. Call ID: {call_id}")

# Polling for call completion
call_status = "unknown"
max_wait_time = 180  # seconds
poll_interval = 5
elapsed = 0

while elapsed < max_wait_time:
    details_url = f'https://api.bland.ai/v1/calls/{call_id}'
    details_response = requests.get(details_url, headers=headers)
    if details_response.status_code == 200:
        details = details_response.json()
        call_status = details.get("status")
        print(f"🔄 Call status: {call_status} (elapsed: {elapsed}s)")

        if call_status == "completed":
            break
    else:
        print("⚠️ Failed to fetch call details. Retrying...")

    time.sleep(poll_interval)
    elapsed += poll_interval
else:
    print("❌ Timed out waiting for call to complete.")
    exit()

# Get transcript
transcript = details.get("concatenated_transcript", "")
details["transcript"] = transcript


# Extract JSON from Gemini response safely
def extract_json_from_response(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
    return None


# Analyze call transcript
def analyze_transcript_with_gemini(transcript):
    prompt = f"""
You are an AI assistant analyzing a customer support call transcript from a bank. Here is the transcript:

\"\"\"{transcript}\"\"\"

Please provide:

1. **Summary** of what the conversation is about.
2. Identify if the customer mentioned **any repayment date** or a specific **time commitment**.
3. Mention any **issues or concerns** raised by the customer.
4. Check if the customer **inquired about the amount due** or remaining balance, and if the bot **responded with a specific amount**. If so, include both the **question and the amount stated**.
5. Perform **sentiment analysis**:
   - Classify the overall tone of the call as **Positive**, **Neutral**, or **Negative**.
   - List all **topics discussed** during the call.
   - List any **problems raised** by the customer.

Respond ONLY with valid JSON. Do not include explanations, duplicates, or extra text. The JSON format is:

{{
  "summary": "...",
  "repayment_date": "...",
  "issues": "...",
  "amount_due_discussion": {{
    "customer_question": "...",
    "bot_response": "..."
  }},
  "sentiment": {{
    "tone": "Positive/Neutral/Negative",
    "topics_discussed": ["..."],
    "problems_raised": ["..."]
  }}
}}
"""

    try:
        response = gemini.generate_content(prompt)
        raw_text = response.text.strip()
        print("📄 Gemini raw response:\n", raw_text)

        parsed = extract_json_from_response(raw_text)
        if parsed:
            return parsed
        else:
            raise ValueError("Unable to parse clean JSON.")
    except Exception as e:
        print(f"⚠️ Gemini analysis failed: {e}")
        return {
            "summary": "",
            "repayment_date": "",
            "issues": "",
            "sentiment": {
                "tone": "Unknown",
                "topics_discussed": [],
                "problems_raised": []
            }
        }

# Run Gemini analysis
if transcript:
    gemini_results = analyze_transcript_with_gemini(transcript)
    details["summary"] = gemini_results.get("summary", "")
    details["repayment_date"] = gemini_results.get("repayment_date", "")
    details["issues"] = gemini_results.get("issues", "")
    details["sentiment"] = gemini_results.get("sentiment", {})
    details["amount_due_discussion"] = gemini_results.get("amount_due_discussion", {})
else:
    details["summary"] = ""
    details["repayment_date"] = ""
    details["issues"] = ""
    details["sentiment"] = {}
    details["amount_due_discussion"] = {}
# Save call details JSON
filename = f'call_details_{call_id}.json'
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(details, f, indent=2)
print(f"📁 Call details saved to {filename}")

# Download recording if available
recording_url = details.get("recording_url")
if recording_url:
    audio = requests.get(recording_url)
    if audio.status_code == 200:
        audio_file = f"call_recording_{call_id}.mp3"
        with open(audio_file, 'wb') as f:
            f.write(audio.content)
        print(f"🎧 Recording saved to {audio_file}")
    else:
        print("⚠️ Failed to download recording.")
else:
    print("ℹ️ No recording URL found yet.")

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
        print("📧 Reminder email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# Try to parse repayment date and schedule email
repayment_date_raw = gemini_results.get("repayment_date")
if repayment_date_raw:
    try:
        # Try parsing the date (it can be "June 5th", "May 30", etc.)
        repayment_dt = dateutil.parser.parse(repayment_date_raw, fuzzy=True)
        repayment_dt = repayment_dt.replace(hour=18, minute=17)  # Default time: 9:00 AM

        print(f"📆 Scheduling email for: {repayment_dt}")

        scheduler = BackgroundScheduler()
        scheduler.start()
        scheduler.add_job(send_reminder_email, 'date', run_date=repayment_dt, args=[gemini_results["summary"], repayment_date_raw])

    except Exception as e:
        print(f"⚠️ Could not schedule email. Date parsing failed: {e}")
else:
    print("ℹ️ No repayment date found; skipping email scheduling.")
