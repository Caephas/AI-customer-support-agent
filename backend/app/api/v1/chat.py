from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.services.chat import save_chat, check_cached_response, process_chat_async
from celery.result import AsyncResult
from backend.app.services.chat import celery_app

router = APIRouter()

# ✅ Define API Request Model
class ChatRequest(BaseModel):
    user_id: str
    message: str

@router.post("/query")
def query_chatbot(request: ChatRequest):
    """Handles user chat queries via AI chatbot."""
    
    # ✅ Check cache first before sending to Celery
    cached_response = check_cached_response(request.user_id, request.message)
    
    if cached_response:
        return {
            "response": cached_response,
            "category": "cached"
        }
    
    # ✅ If not cached, send to Celery for async processing
    task = process_chat_async.delay(request.user_id, request.message)
    
    return {
        "task_id": task.id,
        "response": "Processing your request...",
        "category": "pending"
    }

@router.get("/query/status/{task_id}")
def get_chat_status(task_id: str):
    """Check the status of an AI processing task."""
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == "PENDING":
        return {
            "task_id": task_id,
            "status": "pending",
            "response": "Processing your request..."
        }
    
    elif task_result.state == "SUCCESS":
        return {
            "task_id": task_id,
            "status": "completed",
            "response": task_result.result  # ✅ Return actual task result
        }

    elif task_result.state == "FAILURE":
        return {
            "task_id": task_id,
            "status": "failed",
            "response": str(task_result.result)
        }

    return {
        "task_id": task_id,
        "status": task_result.state,
        "response": "Unknown status"
    }
@router.post("/save")
def store_chat(request: ChatRequest):
    """Manually saves a chat message."""
    return save_chat(request.user_id, request.message, request.response, "general")