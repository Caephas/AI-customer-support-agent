from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.integrations.slack import send_slack_message  
from backend.app.integrations.sendgrid import send_email
from backend.app.integrations.twillo import send_sms, send_whatsapp


router = APIRouter()

class SlackMessage(BaseModel): 
    message: str


class EmailRequest(BaseModel):
    to_email: str 
    subject: str
    message: str

class TwilioMessage(BaseModel):
    recipient: str
    message: str

@router.post("/slack")
def send_slack(request: SlackMessage):
    """Sends a Slack message to the support channel."""
    response = send_slack_message(request.message)
    
    if response["status"] == "error":
        raise HTTPException(status_code=400, detail=response["detail"])
    
    return response


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