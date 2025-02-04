from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.integrations.slack import send_slack_message  
from backend.app.integrations.sendgrid import send_email


router = APIRouter()

class SlackMessage(BaseModel):
    message: str

class EmailRequest(BaseModel):
    to_email: str
    subject: str
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