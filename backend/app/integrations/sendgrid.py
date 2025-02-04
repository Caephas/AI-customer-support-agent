import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()

# Load SendGrid credentials
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")

def send_email(to_email, subject, message):
    """Sends an email via SendGrid."""
    try:
        email = Mail(
            from_email=SENDGRID_FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            plain_text_content=message
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(email)
        return {"status": "success", "status_code": response.status_code}
    except Exception as e:
        return {"status": "error", "detail": str(e)}