import os
import google.generativeai as genai
from datetime import datetime
from app.utils import extract_json_from_response
from dotenv import load_dotenv

load_dotenv

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

def analyze_transcript(transcript: str):
    today = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""
You are an AI assistant analyzing a customer support call transcript from a bank. Here is the transcript:

\"\"\"{transcript}\"\"\"

Please extract the following:
1. Summary of the call.
2. Any mentioned repayment date (even if relative like "tomorrow", return the actual date in YYYY-MM-DD format).
3. Issues raised by customer.
4. Did customer ask about amount due? If yes, what did bot reply?
5. Sentiment details.

Important: Always convert relative dates like "tomorrow" or "next week" into absolute ISO date format (YYYY-MM-DD), assuming the current date is {today}.

Respond in JSON only:
{{
  "summary": "...",
  "repayment_date": "YYYY-MM-DD",
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
        res = model.generate_content(prompt)
        return extract_json_from_response(res.text)
    except Exception as e:
        print("Gemini error:", e)
        return {}
