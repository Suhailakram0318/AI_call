import os
import requests
import inflect
from datetime import datetime
from app.utils import normalize_phone
from dotenv import load_dotenv

load_dotenv()

headers = {'Authorization': f'Bearer {os.getenv("BLAND_API_KEY")}'}

# Utility to convert number to readable words (e.g., 2000 -> two thousand)
p = inflect.engine()

def initiate_call(name: str, phone: str, due_amount: str, due_date: str):
    phone = normalize_phone(phone)

    # Assuming due_amount and due_date are strings
    formatted_amount = format_amount_readable(due_amount) + " rupees"
    formatted_due_date = format_date_readable(due_date)

    payload = {
        "phone_number": phone,
        "voice": "Shashi Tharoor",
        "wait_for_greeting": False,
        "record": True,
        "answered_by_enabled": True,
        "noise_cancellation": True,
        "interruption_threshold": 100,
        "block_interruptions": False,
        "max_duration": 12,
        "model": "base",
        "language": "en",
        "background_track": "office",
        "voicemail_action": "hangup",
        "task": f"""
Goal: Call customers to remind them of their overdue loan payment. Confirm when they can make the payment, assess their willingness and financial condition, and warn about consequences if they refuse or delay.

Call Flow:

1. Introduce yourself and say you're calling from Aindriya Bank regarding an overdue loan payment.
2. Confirm you're speaking with the right person (use their name).
3. Inform them that their recent loan payment of ₹{due_amount} (rupees) was due on {formatted_due_date} and is now overdue.
4. Ask them when they will be able to make the payment.
5. If they give vague responses, delays, or excuses:
   - Ask about their current financial condition.
   - Confirm if they genuinely can't pay or are choosing to delay payment.
   - Ask for the earliest possible repayment date.
6. If they continue avoiding payment or making unreasonable excuses:
   - Warn them that legal action will be initiated.
   - Inform them their CIBIL score will be affected.
   - Mention that collection agents may be dispatched to their registered address.
7. Repeat the urgency and consequences, and be persistent.
8. End the call by summarizing the discussed repayment date and thanking them.

Background:

I am an AI assistant created by Aindriya Bank to follow up on overdue loan repayments. Ensuring timely recovery helps protect the customer’s credit history and supports the bank’s financial ecosystem. This call is a formal notice and part of the escalation process in case of non-compliance.
""",
        "first_sentence": f"Hello, this is Aindriya Bank calling. Am I speaking with {name}? I'm calling regarding an overdue amount of {formatted_amount} that was due by {formatted_due_date}."
    }
    response = requests.post("https://api.bland.ai/v1/calls", json=payload, headers=headers)
    return response.json().get("call_id")

def format_amount_readable(amount):
    try:
        return p.number_to_words(int(amount), andword="").replace(",", "")
    except:
        return str(amount)

def format_date_readable(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%B %d, %Y")  # e.g., "June 1, 2025"
    except:
        return date_str

def check_bland_call_status(call_id: str):
    try:
        response = requests.get(f"https://api.bland.ai/v1/calls/{call_id}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("status"), data.get("concatenated_transcript", "")
        return "error", ""
    except:
        return "error", ""
