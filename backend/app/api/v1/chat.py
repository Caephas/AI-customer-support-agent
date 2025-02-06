from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.services.chat import save_chat, chatbot_graph
from langchain.schema import HumanMessage

router = APIRouter()

# ✅ Define API Request Model
class ChatRequest(BaseModel):
    user_id: str
    message: str

@router.post("/query")
def query_chatbot(request: ChatRequest):
    """Handles user chat queries via AI chatbot."""
    chat_state = {
        "user_id": request.user_id,
        "chat_history": [HumanMessage(content=request.message)],
        "response": "",
        "category": ""
    }

    # ✅ Ensure chatbot graph is invoked correctly
    response_state = chatbot_graph.invoke(chat_state)

    # ✅ Save chat history
    save_chat(
        request.user_id,
        request.message,
        response_state["response"],
        response_state["category"]
    )

    return {
        "response": response_state["response"],
        "category": response_state["category"]
    }

@router.post("/save")
def store_chat(request: ChatRequest):
    """Manually saves a chat message."""
    return save_chat(request.user_id, request.message, request.response, "general")