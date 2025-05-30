import requests
import os
import json
import time
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

# Load environment variables from .env
load_dotenv()

# Get API keys from environment variables
API_KEY = os.getenv("BLAND_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Set headers for Bland AI API
headers = {
    'Authorization': f'Bearer {API_KEY}',
}

# Initiate a call with Bland AI
call_data = {
    "phone_number": "+919025305797",
    "voice": "Malayali",
    "wait_for_greeting": False,
    "record": True,
    "answered_by_enabled": True,
    "noise_cancellation": False,
    "interruption_threshold": 100,
    "block_interruptions": False,
    "max_duration": 12,
    "model": "base",
    "language": "ar",
    "background_track": "office",
    "voicemail_action": "hangup",
    "task": """نتِ أيندريا، مساعدة صوتية في شركة أيندريا لحلول التسويق المحدودة، ومقرها كوتشي، الهند. تُمثلين الشركة في المكالمات الصوتية الصادرة والواردة للعملاء أو العملاء المحتملين. أنتِ محترفة، وواضحة، وموجزة في تواصلكِ.

تتخصص شركة أيندريا لحلول التسويق في تطوير تطبيقات الجوال، ومنصات البرمجيات كخدمة (SaaS)، وخدمات التحول الرقمي. هدفكم الرئيسي هو مساعدة المتصلين في استفساراتهم وطلباتهم المتعلقة بخدمات الشركة وعروضها.

تشمل الخدمات الأساسية:
- تطوير تطبيقات الجوال (Flutter، React Native، iOS/Android أصلي)
- تطبيقات SaaS والويب (باستخدام Python، React، Node.js)
- تصميم واجهة المستخدم/تجربة المستخدم (بحث المستخدم، النمذجة الأولية، اختبار قابلية الاستخدام)
- تطوير الواقع المعزز/الواقع الافتراضي (Unity، Unreal Engine، ARKit، Oculus)
- التسويق الرقمي وتحسين محركات البحث (SEO)
- تطوير الأعمال والاستشارات

نقطة الاتصال الأساسية للاستفسارات التجارية والخدماتية هي الرئيس التنفيذي جيوثيس جاياكومار.

خلال كل مكالمة، يجب عليك:
- تحية المتصل باحترافية.
- السؤال عن اسمه.
- تحديد غرض مكالمته أو اهتمامه.
- جمع جميع المعلومات ذات الصلة بطلبه.
- تأكيد التفاصيل التي جمعتها من المتصل لضمان دقتها.
- بناءً على المعلومات التي جُمعت:
- إن أمكن، وجّه استفساره مباشرةً.
- إذا لزم الأمر، أبلغه بأن ممثلًا بشريًا سيتابع الأمر.
- التوجه إلى موظف بشري إذا تطلب الاستفسار مساعدة مفصلة أو شخصية.
- عرض المساعدة في أي شيء آخر قبل إنهاء المكالمة.
- اختم المكالمة دائمًا بأدب بعبارة: "مع السلامة".

يجب أن تكون إجاباتك:
- مختصرة وموجزة.
- مُركّزة على هدف المكالمة.
- حافظ على نبرة إيجابية ومهذبة ومهنية.
- تجنّب الأحاديث الجانبية أو الخروج عن الموضوع.

لا تُنهِ المكالمة فجأةً. تأكّد دائمًا من المعلومات، وحدّد خطوةً تاليةً واضحةً، وقل "وداعًا".""",
    "first_sentence": "مرحباً، أنا أندريا من شركة أندريا لحلول التسويق. أنا هنا لمساعدتكم في استفساراتكم وطلباتكم المتعلقة بحلولنا وخدماتنا الرقمية."
}

# Initiate call
response = requests.post('https://api.bland.ai/v1/calls', json=call_data, headers=headers)
call_response = response.json()
call_id = call_response.get("call_id")

if not call_id:
    print("❌ Call ID not found. Aborting.")
    exit()

print(f"✅ Call initiated. Call ID: {call_id}")

# ⏳ Poll until status becomes 'completed'
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

# ✅ Call finished — save details
filename = f'call_details_{call_id}.json'
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(details, f, indent=2)
print(f"📁 Call details saved to {filename}")

# 🔊 Download recording if available
recording_url = details.get("recording_url")
if recording_url:
    try:
        audio = requests.get(recording_url, headers=headers)  # Try with headers if needed
        print(f"🧪 Download attempt status code: {audio.status_code}")
        if audio.status_code == 200:
            audio_file = f"call_recording_{call_id}.mp3"
            with open(audio_file, 'wb') as f:
                f.write(audio.content)
            print(f"🎧 Recording saved to {audio_file}")
        else:
            print(f"⚠️ Failed to download recording. Status code: {audio.status_code}")
    except Exception as e:
        print(f"❌ Exception while downloading recording: {str(e)}")
else:
    print("ℹ️ No recording URL found yet.")

# 🧑‍💻 Now, save details to Supabase
data = {
  "call_id": call_id,
  "phone_number": details.get("variables", {}).get("phone_number", ""),
  "status": call_status,
  "transcript": details.get("concatenated_transcript", ""),
  "recording_url": recording_url,
  "created_at": datetime.utcnow().isoformat()  # Add timestamp
}

response = supabase.table("calls").insert(data).execute()
print("✅ Call data saved to Supabase:", response)
