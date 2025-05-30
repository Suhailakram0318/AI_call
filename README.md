# 📞 AI Calling Assistant - Aindriya Bank

An AI-powered voice assistant platform that initiates automated calls to customers, analyzes the call transcript using Google's Gemini API, and schedules repayment reminder emails based on the customer's response.

---

## 🚀 Features

- ✅ Initiate calls using [Bland AI](https://www.bland.ai/)
- ✅ Web UI for single and bulk call uploads
- ✅ Transcripts analyzed via [Gemini 2.0 Flash](https://ai.google.dev/)
- ✅ Natural language repayment date parsing (e.g., "tomorrow", "next week")
- ✅ Auto-scheduled reminder emails via SMTP
- ✅ Deployed on [Render.com](https://render.com)

---

## 🖥️ UI Overview

- **Single Call Form**: Enter name and phone number to start a call.
- **Bulk Upload**: Upload a CSV/XLSX file with `name` and `phone` columns.
- **Live Status**: View real-time updates like:
  - 📞 Initiating...
  - ✅ Call Completed
  - ❌ Rejected
  - ⚠️ Timeout

---

## 📁 Folder Structure

