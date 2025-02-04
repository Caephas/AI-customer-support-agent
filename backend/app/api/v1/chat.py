from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.services.chat import process_chat_query, save_chat

router = APIRouter()

# Define request body schema - Only user_id and message should be required
class ChatRequest(BaseModel):
    user_id: str
    message: str 

@router.post("/query")
def query_chatbot(request: ChatRequest):
    """Processes user chat query and returns AI response."""
    response = process_chat_query(request.user_id, request.message)
    return response


# Separate request model for chat saving (because response is needed when saving)
class ChatSaveRequest(BaseModel):
    user_id: str
    message: str
    response: str

@router.post("/save")
def store_chat(request: ChatSaveRequest):
    """Saves a chat message and response to Firestore."""
    return save_chat(request.user_id, request.message, request.response)