from datetime import datetime, timezone
from backend.app.core.firebase import db
import ollama
from langchain.schema import AIMessage, HumanMessage, SystemMessage


def save_chat(user_id: str, message: str, response: str):
    """Stores user chat messages in Firestore."""
    chat_data = {
        "user_id": user_id,
        "message": message,
        "response": response,
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


def process_chat_query(user_id: str, message: str):
    """Generates AI response using Ollama and stores it in Firestore."""

    # Fetch chat history
    history = fetch_chat_history(user_id)
    
    # Prepare messages for LLM context
    messages = "You are a customer support AI. Here is the conversation history:\n"
    
    for chat in reversed(history):
        messages += f"User: {chat['message']}\nAI: {chat['response']}\n"

    # Add new user query
    messages += f"User: {message}\nAI:"

    # Generate AI response using Ollama
    ai_response = ollama.generate(model="llama3.1:8b", prompt=messages)

    # Extract the actual response
    response_text = ai_response["response"]  
    
    # Store conversation in Firestore
    chat_data = {
        "user_id": user_id,
        "message": message,
        "response": response_text,
        "timestamp": datetime.now(timezone.utc)
    }
    db.collection("chats").add(chat_data)

    return {"response": response_text}  # ✅ Returning correct JSON format