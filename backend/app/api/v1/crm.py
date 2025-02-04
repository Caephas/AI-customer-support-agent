from fastapi import APIRouter, HTTPException, Query
from backend.app.integrations.salesforce import get_customer_details, get_customer_cases, get_salesforce_instance

router = APIRouter()

@router.get("/salesforce/customer")
def fetch_customer(email: str = Query(..., description="Customer email")):
    """Fetches customer details from Salesforce."""
    customer = get_customer_details(email)
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {"customer": customer}

@router.get("/salesforce/cases")
def fetch_cases(email: str = Query(..., description="Customer email")):
    """Fetches customer support cases from Salesforce."""
    cases = get_customer_cases(email)
    
    if not cases:
        raise HTTPException(status_code=404, detail="No cases found")
    
    return {"cases": cases}

@router.post("/salesforce/create-customer")
def create_dummy_customer():
    """Creates a test customer in Salesforce."""
    sf = get_salesforce_instance()
    if isinstance(sf, dict) and "error" in sf:
        raise HTTPException(status_code=500, detail=sf["error"])
    
    new_contact = {
        "FirstName": "Arinze",
        "LastName": "Obidiegwu",
        "Email": "arinze@terminaltech.com",
        "Phone": "+2348027713127"
    }
    
    result = sf.Contact.create(new_contact)
    return {"contact_id": result.get("id"), "message": "Customer created successfully"}

@router.post("/salesforce/create-case")
def create_dummy_case():
    """Creates a test support case in Salesforce."""
    sf = get_salesforce_instance()
    if isinstance(sf, dict) and "error" in sf:
        raise HTTPException(status_code=500, detail=sf["error"])

    # Fetch the test customer ID
    query = "SELECT Id FROM Contact WHERE Email = 'caephas@terminaltech.com' LIMIT 1"
    result = sf.query(query)
    
    if not result["records"]:
        raise HTTPException(status_code=404, detail="Test customer not found. Create a customer first.")

    contact_id = result["records"][0]["Id"]

    # Create a new case linked to the customer
    new_case = {
        "Subject": "Billing Issue",
        "Status": "Open",
        "Description": "Customer having issues selecting cards for payment",
        "Origin": "Web",
        "ContactId": contact_id
    }

    case_result = sf.Case.create(new_case)
    return {"case_id": case_result.get("id"), "message": "Case created successfully"}