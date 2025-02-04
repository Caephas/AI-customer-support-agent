from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.app.core.security import verify_token
from backend.app.services.chat import process_chat_query, save_chat

router = APIRouter()

# Define request body schema - Only user_id and message should be required
class ChatRequest(BaseModel):
    user_id: str
    message: str 

@router.post("/query")
def query_chatbot(request: ChatRequest, user=Depends(verify_token)):
    """Processes user chat query. Requires authentication."""
    if request.user_id != user.uid:
        raise HTTPException(status_code=403, detail="Access denied")
    return process_chat_query(request.user_id, request.message)


# Separate request model for chat saving (because response is needed when saving)
class ChatSaveRequest(BaseModel):
    user_id: str
    message: str 
    response: str

@router.post("/save") 
def store_chat(request: ChatSaveRequest):
    """Saves a chat message and response to Firestore."""
    return save_chat(request.user_id, request.message, request.response)