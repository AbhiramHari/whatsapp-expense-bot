from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client using your API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/whatsapp", methods=['POST'])
def whatsapp_webhook():
    incoming_msg = request.values.get('Body', '').strip()
    print("Received message:", incoming_msg)

    # Create the prompt
    prompt = f"""Extract the expense information from this text in JSON format:
Text: "{incoming_msg}"
Output format: {{ "amount": float, "category": string, "description": string }}"""

    # Send prompt to OpenAI
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Extract content from OpenAI response
    result = response.choices[0].message.content

    # Create a Twilio WhatsApp reply
    twilio_response = MessagingResponse()
    twilio_response.message(f"Logged:\n{result}")
    return str(twilio_response)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
