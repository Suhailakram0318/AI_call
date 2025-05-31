import os
import requests
from app.utils import normalize_phone

headers = {'Authorization': f'Bearer {os.getenv("BLAND_API_KEY")}'}

def initiate_call(name: str, phone: str, amount: str, due_date: str):
    phone = normalize_phone(phone)
    payload = {
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
        "task": f"""We're reaching out to remind you that your recent loan payment of ₹{amount} is currently overdue.
This payment was due by {due_date}. Please confirm when you will be able to make this payment.
Let us know if you're facing any issues that might affect repayment.""",
        "first_sentence": f"Hello, this is Aindriya Bank calling. Am I speaking with {name}? I'm calling regarding an overdue amount of ₹{amount} due by {due_date}."
    }
    response = requests.post("https://api.bland.ai/v1/calls", json=payload, headers=headers)
    return response.json().get("call_id")

def check_bland_call_status(call_id: str):
    try:
        response = requests.get(f"https://api.bland.ai/v1/calls/{call_id}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("status"), data.get("concatenated_transcript", "")
        return "error", ""
    except:
        return "error", ""
