from datetime import datetime, timezone

from backend.app import db

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