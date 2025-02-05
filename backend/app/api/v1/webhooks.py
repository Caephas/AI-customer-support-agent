import xml.etree.ElementTree as ET
from fastapi import APIRouter, Response, Request
from backend.app.integrations.slack import send_slack_message
from backend.app.integrations.twillo import send_whatsapp
from backend.app.integrations.sendgrid import send_email
from backend.app.core.firebase import db
from datetime import datetime, timezone

router = APIRouter()

@router.post("/salesforce-webhook")
async def receive_salesforce_webhook(request: Request):
    """Handles incoming Salesforce case updates from Salesforce Outbound Messages."""
    try:
        # Read and parse the XML request body
        raw_body = await request.body()
        xml_data = raw_body.decode("utf-8")
        print("📩 Raw XML from Salesforce:\n", xml_data)

        # Parse XML
        root = ET.fromstring(xml_data)
        ns = {"sf": "urn:sobject.enterprise.soap.sforce.com"}

        case_id = root.find(".//sf:Id", ns).text
        status = root.find(".//sf:Status", ns).text
        subject = root.find(".//sf:Subject", ns).text

        print(f"✅ Case Updated → ID: {case_id}, Status: {status}, Subject: {subject}")

        # **🔹 Automate Actions Based on Case Status**
        
        # 1️⃣ **Log the event in Firebase**
        log_salesforce_event(case_id, status, subject)

        # 2️⃣ **Send Slack Alert for Escalated Cases**
        if status.lower() == "escalated":
            slack_message = f"🚨 *Case Escalated!*\n🆔 Case ID: {case_id}\n📌 Subject: {subject}\n⚠ Status: {status}"
            send_slack_message(slack_message)

        # 3️⃣ **Send WhatsApp Update to Customer**
        if status.lower() in ["escalated", "working"]:
            customer_phone = "+1234567890"  # Replace with actual phone field
            whatsapp_message = f"🔔 Your support case '{subject}' has been updated to *{status}*. Support will contact you soon."
            send_whatsapp(customer_phone, whatsapp_message)

        # 4️⃣ **Send an Email Confirmation if Case is Closed**
        if status.lower() == "closed":
            customer_email = "customer@example.com"  # Replace with actual email field
            email_subject = f"Case {case_id} Closed - {subject}"
            email_body = f"Dear Customer,\n\nYour case '{subject}' has been resolved. If you have further issues, feel free to contact us.\n\nBest Regards,\nCustomer Support"
            send_email(customer_email, email_subject, email_body)

        # Return XML response required by Salesforce
        return Response(content="""<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
            <soapenv:Body>
                <notificationsResponse xmlns="http://soap.sforce.com/2005/09/outbound">
                    <Ack>true</Ack>
                </notificationsResponse>
            </soapenv:Body>
        </soapenv:Envelope>""",
        media_type="application/xml")

    except Exception as e:
        print(f"❌ Error processing webhook: {str(e)}")
        return Response(
            content="""<?xml version="1.0" encoding="UTF-8"?>
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
                <soapenv:Body>
                    <notificationsResponse xmlns="http://soap.sforce.com/2005/09/outbound">
                        <Ack>false</Ack>
                    </notificationsResponse>
                </soapenv:Body>
            </soapenv:Envelope>""",
            media_type="application/xml",
            status_code=500
        )

# **Helper Function to Log Webhook Events in Firebase**
def log_salesforce_event(case_id, status, subject):
    """Log webhook event into Firebase Firestore."""
    event = {
        "case_id": case_id,
        "status": status,
        "subject": subject,
        "timestamp": datetime.now(timezone.utc)
    }
    db.collection("salesforce_logs").add(event)
    print(f"✅ Logged case {case_id} update in Firestore.")