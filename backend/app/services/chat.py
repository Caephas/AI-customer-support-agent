from datetime import datetime, timezone
from typing import TypedDict, List, Union
import ollama
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from backend.app.core.firebase import db

# ✅ Define AI Chatbot State
class ChatState(TypedDict):
    user_id: str
    chat_history: List[Union[HumanMessage, AIMessage]]
    response: str
    category: str  # billing, technical, general, escalation

# ✅ Initialize AI Model (Ollama - Llama3)
chat_model = ollama.chat(model="llama3.1:8b")

def classify_query(message: str) -> str:
    """Classifies the query into billing, technical, general, or escalation."""
    
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
def fetch_chat_history(user_id: str) -> List[Union[HumanMessage, AIMessage]]:
    """Fetches the last 5 chat messages for context-aware responses."""
    chats = (
        db.collection("chats")
        .where("user_id", "==", user_id)
        .order_by("timestamp", direction="DESCENDING")
        .limit(5)
        .stream()
    )
    return [
        HumanMessage(content=chat.to_dict()["message"]) if i % 2 == 0 else AIMessage(content=chat.to_dict()["response"])
        for i, chat in enumerate(chats)
    ]


def generate_response(state: ChatState) -> ChatState:
    """Generates AI response based on user query & chat history."""
    history = fetch_chat_history(state["user_id"])

    messages = [SystemMessage(content="You are a customer support AI.")]
    messages.extend(history)
    messages.append(HumanMessage(content=state["chat_history"][-1].content))

    # Generate AI response
    ai_response = chat_model.invoke(messages)
    response_text = ai_response.content

    return {
        "user_id": state["user_id"],
        "chat_history": state["chat_history"],
        "response": response_text,
        "category": classify_query(state["chat_history"][-1].content)
    }
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

def human_escalation(state: ChatState) -> ChatState:
    """Routes query to human agent if AI is unsure."""
    print("🚨 Escalating to human agent for:", state["chat_history"][-1].content)
    return {
        "user_id": state["user_id"],
        "chat_history": state["chat_history"],
        "response": "Escalating to a human agent.",
        "category": "escalation"
    }

graph = StateGraph(ChatState)

graph.add_node("generate_response", generate_response)
graph.add_node("human_escalation", human_escalation)

# **Conditionally Escalate to a Human Agent**
def route_chat(state: ChatState):
    if state["category"] == "escalation":
        return "human_escalation"
    return END

graph.set_entry_point("generate_response")
graph.add_conditional_edges("generate_response", route_chat)
graph.add_edge("human_escalation", END)

# ✅ Compile AI Chatbot
chatbot = graph.compile()