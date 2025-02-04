import os
from simple_salesforce import Salesforce
from dotenv import load_dotenv
from backend.app.integrations.sendgrid import send_email

load_dotenv()

# Load Salesforce credentials
CLIENT_ID = os.getenv("SALESFORCE_CLIENT_ID")
CLIENT_SECRET = os.getenv("SALESFORCE_CLIENT_SECRET")
USERNAME = os.getenv("SALESFORCE_USERNAME")
PASSWORD = os.getenv("SALESFORCE_PASSWORD")
SECURITY_TOKEN = os.getenv("SALESFORCE_SECURITY_TOKEN")
AUTH_URL = os.getenv("SALESFORCE_AUTH_URL")

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

def create_salesforce_ticket(email, subject, description):
    """Creates a new support case in Salesforce and sends email confirmation."""
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

    # **Send confirmation email to customer**
    send_email(email, "Support Ticket Created", f"Your ticket '{subject}' has been created!")

    return {"case_id": case_result.get("id"), "message": "Case created successfully"}