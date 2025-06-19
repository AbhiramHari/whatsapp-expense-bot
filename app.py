from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get("Body", "")
    print("Received message:", incoming_msg)

    # Prompt OpenAI for structured JSON response
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=
        [

            {"role": "system", "content": 
                
                (
                "You are an expense tracking assistant helping the user log and categorize their spending. "
                "Your job is to extract structured information from each message and respond in a hybrid format:\n\n"
                "1. Identify amount, merchant, and category from the message (e.g. 'Spent $30 at Kroger').\n"
                "2. Reply with a friendly confirmation like: `Got it! $30 spent at Kroger categorized as Groceries.`\n"
                "3. Then output a valid JSON block on a new line for spreadsheet use:\n"
                "{\n  \"amount\": float,\n  \"merchant\": string,\n  \"category\": string,\n  \"description\": string\n}\n"
                "4. Use these categories: Groceries, Dining, Transport, Shopping, Bills, Entertainment, Health, Travel, Utilities, Other.\n"
                "5. If the user corrects the category (e.g. 'No, that should be Entertainment'), update the previous entry, confirm the update, and resend the corrected JSON.\n"
                "Always keep your response concise, friendly, and well-formatted."
                )
            },
            {"role": "user", "content": incoming_msg}
        ]
    )

    # Format and send Twilio response
    reply = response.choices[0].message["content"].strip()
    twilio_resp = MessagingResponse()
    twilio_resp.message(f"Logged:\n{reply}")
    return str(twilio_resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
