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
        messages=[
            {
                "role": "system",
                "content": (
                    "You're a financial assistant. Extract expense information from the message "
                    "and respond with a JSON object in the format: "
                    "{ 'amount': float, 'category': string, 'description': string }. "
                    "Be concise and accurate."
                )
            },
            {"role": "user", "content": incoming_msg}
        ]
    )

    # Format and send Twilio response
    reply = response.choices[0].message.content.strip()
    twilio_resp = MessagingResponse()
    twilio_resp.message(f"Logged:\n{reply}")
    return str(twilio_resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
