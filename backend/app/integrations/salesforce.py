import os
import requests
from simple_salesforce import Salesforce
from dotenv import load_dotenv
from backend.app.integrations.sendgrid import send_email
from backend.app.integrations.twillo import send_whatsapp

load_dotenv()

# Load Salesforce credentials
CLIENT_ID = os.getenv("SALESFORCE_CLIENT_ID")
CLIENT_SECRET = os.getenv("SALESFORCE_CLIENT_SECRET")
USERNAME = os.getenv("SALESFORCE_USERNAME")
PASSWORD = os.getenv("SALESFORCE_PASSWORD")
SECURITY_TOKEN = os.getenv("SALESFORCE_SECURITY_TOKEN")
AUTH_URL = os.getenv("SALESFORCE_AUTH_URL")
SALESFORCE_ACCESS_TOKEN = os.getenv("SALESFORCE_ACCESS_TOKEN")
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

def get_salesforce_instance():
    """Authenticates and returns a Salesforce instance."""
    try:
        sf = Salesforce(
            username=USERNAME,
            password=PASSWORD,
            security_token=SECURITY_TOKEN,
            client_id=CLIENT_ID
        )
        return sf
    except Exception as e:
        return {"error": str(e)}

def get_customer_details(email):
    """Fetch customer details from Salesforce by email."""
    sf = get_salesforce_instance()
    if isinstance(sf, dict) and "error" in sf:
        return sf

    query = f"SELECT Id, Name, Email, Phone FROM Contact WHERE Email = '{email}'"
    result = sf.query(query)
    return result.get("records", [])

def get_customer_cases(email):
    """Fetch customer support cases from Salesforce."""
    sf = get_salesforce_instance()
    if isinstance(sf, dict) and "error" in sf:
        return sf

    query = f"""
    SELECT Id, Subject, Status, Description
    FROM Case WHERE Contact.Email = '{email}'
    """
    result = sf.query(query)
    return result.get("records", [])

def create_salesforce_ticket(email, subject, description, phone_number):
    """Creates a new support case in Salesforce and sends WhatsApp confirmation."""
    sf = get_salesforce_instance()
    if isinstance(sf, dict) and "error" in sf:
        return sf

    query = f"SELECT Id FROM Contact WHERE Email = '{email}' LIMIT 1"
    result = sf.query(query)
    
    if not result["records"]:
        return {"error": "Customer not found"}

    contact_id = result["records"][0]["Id"]

    new_case = {
        "Subject": subject,
        "Status": "Open",
        "Description": description,
        "Origin": "Web",
        "ContactId": contact_id
    }

    case_result = sf.Case.create(new_case)

    # **Send WhatsApp confirmation to customer**
    send_whatsapp(phone_number, f"Your support ticket '{subject}' has been created!")

    return {"case_id": case_result.get("id"), "message": "Case created successfully"}

def subscribe_to_salesforce_events():
    """Subscribes FastAPI to Salesforce Platform Events."""
    headers = {
        "Authorization": f"Bearer {SALESFORCE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "event_type": "salesforce_ticket_created",
        "data": {
            "subject": "Test Case from Salesforce",
            "email": "customer@example.com",
            "phone_number": "+1234567890"
        }
    }
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    return response.json()