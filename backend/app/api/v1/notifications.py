from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.integrations.slack import send_slack_message  
from backend.app.integrations.sendgrid import send_email
from backend.app.integrations.twillo import send_sms, send_whatsapp


router = APIRouter()

# Define Webhook Event Model
class SalesforceWebhook(BaseModel):
    event_type: str
    data: dict


class EmailRequest(BaseModel):
    to_email: str 
    subject: str
    message: str

class TwilioMessage(BaseModel):
    recipient: str
    message: str

@router.post("/slack")
def send_slack_notification(request: SalesforceWebhook):
    """Sends Salesforce case updates to Slack."""
    
    # Extract case details
    case_id = request.data.get("case_id", "Unknown Case ID")
    subject = request.data.get("subject", "No Subject")
    status = request.data.get("status", "No Status")
    email = request.data.get("email", "No Email")
    
    # Format the Slack message
    slack_message = f"""
    🚨 *Salesforce Case Update* 🚨
    *Case ID:* {case_id}
    *Subject:* {subject}
    *Status:* {status}
    *Customer:* {email}
    """

    # Send message to Slack
    response = send_slack_message(slack_message)

    if response["status"] == "error":
        raise HTTPException(status_code=400, detail=response["detail"])
    
    return {"status": "success", "slack_message": slack_message}


@router.post("/email")
def send_email_api(request: EmailRequest):
    """Sends an email via SendGrid."""
    response = send_email(request.to_email, request.subject, request.message)
    
    if response["status"] == "error":
        raise HTTPException(status_code=400, detail=response["detail"])
    
    return response


@router.post("/sms")
def send_sms_api(request: TwilioMessage):
    """Sends an SMS via Twilio."""
    response = send_sms(request.recipient, request.message)
    
    if response.get("status") not in ["queued", "sent", "delivered"]:
        raise HTTPException(status_code=400, detail="Failed to send SMS")
    
    return response

@router.post("/whatsapp")
def send_whatsapp_api(request: TwilioMessage):
    """Sends a WhatsApp message via Twilio."""
    response = send_whatsapp(request.recipient, request.message)
    
    if response.get("status") not in ["queued", "sent", "delivered"]:
        raise HTTPException(status_code=400, detail="Failed to send WhatsApp message")
    
    return response