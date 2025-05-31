import re
import json

def normalize_phone(phone: str):
    phone = str(phone).strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone

def extract_json_from_response(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            return {}
    return {}
