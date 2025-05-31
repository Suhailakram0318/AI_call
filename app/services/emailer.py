import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def send_reminder_email(summary, repayment_date):
    subject = "📬 Loan Repayment Reminder"
    body = f"""Hi,

This is a reminder regarding your scheduled repayment.

Summary from the call:
{summary}

Repayment Date: {repayment_date}

Thank you,
Aindriya Bank"""
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = os.getenv("SMTP_USER")
    msg['To'] = os.getenv("EMAIL_RECIPIENT")

    try:
        with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT", "587"))) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
            server.sendmail(msg['From'], msg['To'], msg.as_string())
        print("✅ Reminder email sent")
    except Exception as e:
        print("❌ Email failed:", e)
