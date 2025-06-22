from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
import json

# Load environment variables
load_dotenv()

# Initialize Flask and OpenAI
app = Flask(__name__)
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Google Sheets logging function
def log_to_google_sheets(amount, merchant, category, description):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("Expenses Tracker Bot").sheet1  # <-- Make sure this name matches your sheet
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, amount, merchant, category, description])

# ✅ Main webhook route
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get("Body", "")
    print("Received message:", incoming_msg)

    # Prompt OpenAI for structured JSON response
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": (
                "You are an expense tracking assistant helping the user log and categorize their spending. "
                "Your job is to extract structured information from each message and respond in a hybrid format:\n\n"
                "1. Identify amount, merchant, and category from the message (e.g. 'Spent $30 at Kroger').\n"
                "2. Reply with a friendly confirmation like: `Got it! $30 spent at Kroger categorized as Groceries.`\n"
                "3. Then output a valid JSON block on a new line for spreadsheet use:\n"
                "{\n  \"amount\": float,\n  \"merchant\": string,\n  \"category\": string,\n  \"description\": string\n}\n"
                "4. Use these categories: Groceries, Dining, Transport, Shopping, Bills, Entertainment, Health, Travel, Utilities, Other.\n"
                "5. If the user corrects the category (e.g. 'No, that should be Entertainment'), update the previous entry, confirm the update, and resend the corrected JSON.\n"
                "Always keep your response concise, friendly, and well-formatted."
            )},
            {"role": "user", "content": incoming_msg}
        ]
    )

    full_reply = response.choices[0].message.content.strip()
    print("GPT reply:\n", full_reply)

    # Extract JSON from the reply
    json_match = re.search(r'\{.*?\}', full_reply, re.DOTALL)
    sheet_success = True

    if json_match:
        try:
            data = json.loads(json_match.group())
            log_to_google_sheets(
                amount=data["amount"],
                merchant=data["merchant"],
                category=data["category"],
                description=data["description"]
            )
        except Exception as e:
            print("❌ Error parsing or logging JSON:", e)
            sheet_success = False

    # Send WhatsApp reply
    twilio_resp = MessagingResponse()
    twilio_resp.message(f"Logged:\n{full_reply}")
    if not sheet_success:
        twilio_resp.message("⚠️ I understood the expense, but had trouble saving it to Google Sheets.")
    return str(twilio_resp)

# ✅ Keep-alive route for uptime monitoring
@app.route("/", methods=["GET"])
def keep_alive():
    return "Expense bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
