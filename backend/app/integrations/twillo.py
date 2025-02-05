import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# Load Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_sms(to, message):
    """Sends an SMS using Twilio."""
    response = client.messages.create(
        body=message,
        from_=TWILIO_PHONE_NUMBER,
        to=to
    )
    return {"message_id": response.sid, "status": response.status}

def send_whatsapp(to, message):
    """Sends a WhatsApp message using Twilio."""
    response = client.messages.create(
        body=message,
        from_=TWILIO_WHATSAPP_NUMBER,
        to=f"whatsapp:{to}"
    )
    return {"message_id": response.sid, "status": response.status}