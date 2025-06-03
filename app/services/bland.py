import os
import requests
from app.utils import normalize_phone
from dotenv import load_dotenv

load_dotenv()

headers = {'Authorization': f'Bearer {os.getenv("BLAND_API_KEY")}'}

def initiate_call(name: str, phone: str, due_amount: str, due_date: str):
    phone = normalize_phone(phone)
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
        "task": f"""We're reaching out to remind you that your recent loan payment of ₹{due_amount} is currently overdue.
This payment was due by {due_date}. Please confirm when you will be able to make this payment.
Let us know if you're facing any issues that might affect repayment.

If the caller avoids payment, gives unreasonable excuses, or seems unwilling to cooperate, the agent should take a firmer tone:
- Warn the caller that legal action will be initiated.
- Inform that their CIBIL credit score will be negatively affected.
- Notify them that physical collection agents may be sent to their registered address.

The agent must ask about:
- Their current financial situation.
- Whether they are genuinely unable to pay or are simply delaying payment despite having funds.
- The earliest possible date they can make the payment.

Be persistent and do not accept vague or evasive answers. Make it clear that this matter is serious and will escalate if not resolved promptly.""",
        "first_sentence": f"Hello, this is Aindriya Bank calling. Am I speaking with {name}? I'm calling regarding an overdue amount of ₹{due_amount} due by {due_date}."
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
