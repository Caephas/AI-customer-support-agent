from datetime import datetime, timezone
from backend.app.core.firebase import db
import ollama
from langchain.schema import AIMessage, HumanMessage, SystemMessage

def save_chat(user_id: str, message: str, response: str, category: str):
    """Stores user chat messages in Firestore."""
    chat_data = {
        "user_id": user_id,
        "message": message,
        "response": response,
        "category": category,
        "timestamp": datetime.now(timezone.utc)
    }
    db.collection("chats").add(chat_data)
    return {"message": "Chat saved"} 

def fetch_chat_history(user_id: str):
    """Fetches the last 5 chat messages for context."""
    chats = (
        db.collection("chats")
        .where("user_id", "==", user_id)
        .order_by("timestamp", direction="DESCENDING")
        .limit(5)
        .stream()
    )
    return [{"message": chat.to_dict()["message"], "response": chat.to_dict()["response"]} for chat in chats]

def classify_query(message: str):
    """Classifies the query into billing, technical, general, or escalation."""
    
    classification_prompt = f"""
    You are a support assistant. Classify the following query into one of these categories:
    - "billing" (if the question is about payments, invoices, refunds)
    - "technical" (if the question is about login issues, bugs, system errors)
    - "general" (if the question is simple and can be answered directly)
    - "escalation" (if the question is unclear or needs human intervention)

    Query: "{message}"
    Reply with only one word: billing, technical, general, or escalation.
    """

    classification_response = ollama.generate(model="llama3.1:8b", prompt=classification_prompt)
    return classification_response["response"].strip().lower()

def process_chat_query(user_id: str, message: str):
    """Routes the query based on classification and generates an AI response."""

    # Classify the query
    category = classify_query(message)

    # Fetch chat history
    history = fetch_chat_history(user_id)
    
    # Prepare messages for LLM context
    messages = f"You are a customer support AI. The user's query is classified as: {category}\n"

    for chat in reversed(history):
        messages += f"User: {chat['message']}\nAI: {chat['response']}\n"

    messages += f"User: {message}\nAI:"

    # AI Response Logic
    if category == "billing":
        ai_response = "Your billing query has been forwarded to our finance team. They will contact you soon."
    elif category == "technical":
        ai_response = "Your technical issue has been sent to our engineering team. Please wait for further updates."
    elif category == "escalation":
        ai_response = "This request requires human intervention. A support agent will assist you shortly."
    else:
        ai_response = ollama.generate(model="llama3.1:8b", prompt=messages)["response"]

    # Store conversation in Firestore
    save_chat(user_id, message, ai_response, category)

    return {"response": ai_response, "category": category}