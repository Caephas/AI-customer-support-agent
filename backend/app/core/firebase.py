import firebase_admin
from firebase_admin import credentials, auth, firestore

# Load Firebase credentials
cred = credentials.Certificate("backend/app/core/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# User Authentication Functions
def create_user(email: str, password: str):
    """Creates a new user in Firebase Auth."""
    user = auth.create_user(email=email, password=password)
    return user

def get_user(uid: str):
    """Fetches user data from Firebase Auth."""
    return auth.get_user(uid)

def delete_user(uid: str):
    """Deletes a user from Firebase Auth."""
    auth.delete_user(uid)

# Firestore Database Functions
def add_document(collection: str, data: dict):
    """Adds a document to a Firestore collection."""
    doc_ref = db.collection(collection).add(data)
    return doc_ref

def get_document(collection: str, doc_id: str):
    """Retrieves a document from Firestore."""
    doc = db.collection(collection).document(doc_id).get()
    if doc.exists:
        return doc.to_dict()
    return None