from datetime import datetime, timezone
from typing import TypedDict, List, Union
import ollama
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from celery import Celery
from backend.app.core.firebase import db
from backend.app.integrations.salesforce import create_salesforce_ticket
from backend.app.integrations.slack import send_slack_message
import time

# ✅ Define AI Chatbot State
class ChatState(TypedDict):
    user_id: str
    chat_history: List[Union[HumanMessage, AIMessage]]
    response: str
    category: str  # billing, technical, general, escalation

# ✅ Initialize Celery Worker
celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["backend.app.services.chat"]
)

celery_app.conf.update(
    task_track_started=True,
    result_backend="redis://localhost:6379/0",
    result_extended=True
)

# ✅ Initialize AI Model (Ollama - Llama3)
chat_model = ollama.chat(model="llama3.1:8b")
# ✅ Format Messages for Ollama
def format_message(message):
    """Formats messages for the Ollama AI model."""
    if isinstance(message, SystemMessage):
        return {"role": "system", "content": message.content}
    elif isinstance(message, HumanMessage):
        return {"role": "user", "content": message.content}
    elif isinstance(message, AIMessage):
        return {"role": "assistant", "content": message.content}
    else:
        return {"role": "user", "content": str(message)}
# ✅ Query Classification Logic
def classify_query(message: str) -> str:
    classification_prompt = f"""
    You are a customer support assistant. Classify the following query into one of these categories:
    - "billing" (if the question is about payments, invoices, refunds)
    - "technical" (if the question is about login issues, bugs, system errors)
    - "general" (if the question is simple and can be answered directly)
    - "escalation" (if the question is unclear or needs human intervention)
    
    Query: "{message}"
    Reply with only one word: billing, technical, general, or escalation.
    """
    classification_response = ollama.generate(model="llama3.1:8b", prompt=classification_prompt)
    return classification_response["response"].strip().lower()

# ✅ Fetch Chat History
def fetch_chat_history(user_id: str) -> List[Union[HumanMessage, AIMessage]]:
    chats = (
        db.collection("chats")
        .where("user_id", "==", user_id)
        .order_by("timestamp", direction="DESCENDING")
        .limit(10)
        .stream()
    )
    return [HumanMessage(content=chat.to_dict()["message"]) if i % 2 == 0 else AIMessage(content=chat.to_dict()["response"]) for i, chat in enumerate(chats)]

# ✅ Check Cached Response
def check_cached_response(user_id: str, message: str) -> str:
    """Checks if a similar query was already answered recently and counts occurrences."""
    
    cached_chats = (
        db.collection("chats")
        .where("user_id", "==", user_id)
        .order_by("timestamp", direction="DESCENDING")
        .limit(5)
        .stream()
    )

    occurrences = 0
    last_response = None

    for chat in cached_chats:
        chat_data = chat.to_dict()
        if chat_data["message"].lower() == message.lower():
            occurrences += 1
            last_response = chat_data["response"]

    # ✅ If it's the first time asking, return None (i.e., no cached response)
    if occurrences == 0:
        return None

    # ✅ If it's the second time asking, give a subtle reminder
    if occurrences == 1:
        return f"You've asked this question before! Here's what I told you:\n\n{last_response}"

    # ✅ If it's the third time or more, be more direct
    return f"You've already asked this {occurrences} times! My previous response was:\n\n{last_response}"

# ✅ AI Response Generation
def generate_response(state: ChatState) -> ChatState:
    """Generates AI response using classification & memory."""
    
    history = fetch_chat_history(state["user_id"])

    messages = [SystemMessage(content="You are a customer support AI.")]
    messages.extend(history)

    last_message = HumanMessage(content=state["chat_history"][-1]["content"])
    messages.append(last_message)

    # ✅ Call AI Model
    ai_response = ollama.chat(model="llama3.1:8b", messages=[format_message(m) for m in messages])
    response_text = ai_response.message.content if ai_response.message else "No response generated"

    # ✅ Categorize Query
    category = classify_query(last_message.content)

    # ✅ If billing, create a Salesforce ticket
    if category == "billing":
        case_id = create_salesforce_ticket(
            email="arinze@terminaltech.com",
            subject="Billing Issue",
            description=last_message.content,
            phone_number="+2348027713127"
        )
        response_text = f"Your billing issue has been reported. Case ID: {case_id}. Our finance team will contact you soon."

    return {
        "user_id": state["user_id"],
        "chat_history": state["chat_history"],
        "response": response_text,
        "category": category
    }

# ✅ Save Chat in Firestore
def save_chat(user_id: str, message: str, response: str, category: str):
    try:
        chat_data = {
            "user_id": user_id,
            "message": message,
            "response": response,
            "category": category,
            "timestamp": datetime.now(timezone.utc)
        }
        db.collection("chats").add(chat_data)
    except Exception as e:
        print(f"❌ Firestore Error: {e}")

# ✅ Process Chat Async
@celery_app.task(name='tasks')
def process_chat_async(user_id: str, message: str):
    """Handles chat requests asynchronously using Celery."""
    
    # ✅ Check cache before processing
    cached_response = check_cached_response(user_id, message)
    if cached_response:
        return {
            "user_id": user_id,
            "chat_history": [{"role": "user", "content": message}],
            "response": cached_response,
            "category": "cached"
        }
    
    # ✅ Prepare chat state
    chat_state = {
        "user_id": user_id,
        "chat_history": [{"role": "user", "content": message}],
        "response": "",
        "category": ""
    }

    # ✅ Generate AI Response
    response = generate_response(chat_state)

    # ✅ Save Chat History to Firestore (caching it)
    if response["response"]:
        save_chat(user_id, message, response["response"], response["category"])
    
    return response

# ✅ Define LangGraph Flow
graph = StateGraph(ChatState)
graph.add_node("generate_response", generate_response)
graph.set_entry_point("generate_response")
graph.add_edge("generate_response", END)
chatbot_graph = graph.compile()