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

def initiate_call(name: str, phone: str, bank_name: str, due_amount: str, due_date: str):
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

1. Greet the person and ask, "Am I speaking with {name}?"
2. If the person says **yes**:
    - Introduce yourself as an assistant from {bank_name}.
    - Inform them that their recent loan payment of {formatted_amount} was due on {formatted_due_date} and is currently overdue.
    - Ask when they will be able to make the payment.
    - If they give vague responses, excuses, or delay:
        - Ask about their current financial condition.
        - Clarify whether they genuinely can't pay or are unwilling to pay.
        - Ask for the earliest possible date they can repay.
    - If they continue avoiding payment or provide unreasonable excuses:
        - Warn that legal action may be initiated.
        - Inform that their CIBIL score will be negatively affected.
        - State that recovery agents may be sent to their registered address.
    - Be firm and persistent. Do not accept vague answers.
    - Repeat the urgency and consequences until a concrete response is received.
    - End the call by summarizing the discussed repayment date and thanking them.

3. If the person says **no**:
    - Politely ask who you are speaking with.
    - Ask if they are related to or can help you contact {name}.
    - If they confirm a relationship (e.g., family), politely ask them to pass on the message that there is an overdue loan payment and the bank is trying to reach {name}.
    - If they are not related or unsure, thank them and end the call.

Background:

I am an AI assistant created by {bank_name} to follow up on overdue loan repayments. Ensuring timely recovery protects the customer's credit history and supports the bank’s financial operations. This call is a formal reminder and may lead to further action in case of continued non-compliance.
""",
        "first_sentence": f"Hello, this is {bank_name} calling. Am I speaking with {name}?"
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
