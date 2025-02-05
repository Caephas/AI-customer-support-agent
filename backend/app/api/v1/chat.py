from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.app.services.chat import save_chat,chatbot
from langchain.schema import HumanMessage

router = APIRouter()

# Define request body schema - Only user_id and message should be required
class ChatRequest(BaseModel):
    user_id: str
    message: str 
# Separate request model for chat saving (because response is needed when saving)
class ChatSaveRequest(BaseModel):
    user_id: str
    message: str 
    response: str

@router.post("/query")
def query_chatbot(request: ChatRequest):
    """Handles user chat queries via AI chatbot."""
    chat_state = {
        "user_id": request.user_id,
        "chat_history": [HumanMessage(content=request.message)],  # ✅ Correct format
        "response": "",  # Placeholder response
        "category": ""
    }

    # ✅ Ensure chatbot graph is invoked correctly
    response_state = chatbot.invoke(chat_state)  # ✅ Use compiled chatbot_graph

    return {
        "response": response_state["response"],
        "category": response_state["category"]
    }
@router.post("/save") 
def store_chat(request: ChatSaveRequest):
    """Saves a chat message and response to Firestore."""
    return save_chat(request.user_id, request.message, request.response) 