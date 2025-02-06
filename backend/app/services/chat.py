from datetime import datetime, timezone
from typing import TypedDict, List, Union
import ollama
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from backend.app.core.firebase import db
from backend.app.integrations.salesforce import create_salesforce_ticket
from backend.app.integrations.slack import send_slack_message

# ✅ Define AI Chatbot State
class ChatState(TypedDict):
    user_id: str
    chat_history: List[Union[HumanMessage, AIMessage]]
    response: str
    category: str  # billing, technical, general, escalation

# ✅ Initialize AI Model (Ollama - Llama3)
chat_model = ollama.chat(model="llama3.1:8b")

# ✅ Query Classification Logic
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

# ✅ Fetch Chat History for Context
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

# ✅ Format Messages for Ollama
def format_message(message):
    if isinstance(message, SystemMessage):
        return {"role": "system", "content": message.content}
    elif isinstance(message, HumanMessage):
        return {"role": "user", "content": message.content}
    elif isinstance(message, AIMessage):
        return {"role": "assistant", "content": message.content}
    else:
        return {"role": "user", "content": str(message)}

# ✅ AI Response Generation
def generate_response(state: ChatState) -> ChatState:
    history = fetch_chat_history(state["user_id"])

    messages = [SystemMessage(content="You are a customer support AI.")]
    messages.extend(history)
    messages.append(HumanMessage(content=state["chat_history"][-1].content))

    # Format messages as expected by Ollama (with 'role' and 'content')
    formatted_messages = [format_message(m) for m in messages]

    # Call ollama.chat with the formatted messages
    ai_response = ollama.chat(model="llama3.1:8b", messages=formatted_messages)
    
    # Instead of ai_response["response"], use the message attribute:
    response_text = ai_response.message.content

    category = classify_query(state["chat_history"][-1].content)

    if category == "billing":
        case_id = create_salesforce_ticket(
            email="arinze@terminaltech.com",
            subject="Billing Issue",
            description=state["chat_history"][-1].content,
            phone_number="+2348027713127"
        )
        response_text = f"Your billing issue has been reported. Case ID: {case_id}. Our finance team will contact you soon."


    return {
        "user_id": state["user_id"],
        "chat_history": state["chat_history"],
        "response": response_text,
        "category": classify_query(state["chat_history"][-1].content)
    }

# ✅ Save Chat in Firestore
def save_chat(user_id: str, message: str, response: str, category: str):
    """Stores user chat messages in Firestore."""
    try:
        chat_data = {
            "user_id": user_id,
            "message": message,
            "response": response,
            "category": category,
            "timestamp": datetime.now(timezone.utc)
        }
        db.collection("chats").add(chat_data)
        return {"message": "Chat saved"}
    except Exception as e:
        print(f"❌ Firestore Error: {e}")
        return {"error": str(e)}

# ✅ Handle Human Escalation
def human_escalation(state: ChatState) -> ChatState:
    """Routes query to human agent if AI is unsure."""
    # print("🚨 Escalating to human agent for:", state["chat_history"][-1].content)
    send_slack_message(
        f"🚨 Escalation Alert!\nUser Query: {state['chat_history'][-1].content}\n"
        "A human agent is needed."
    )
    return {
        "user_id": state["user_id"],
        "chat_history": state["chat_history"],
        "response": "Escalating to a human agent.",
        "category": "escalation"
    }

# ✅ Define LangGraph Flow
graph = StateGraph(ChatState)
graph.add_node("generate_response", generate_response)
graph.add_node("human_escalation", human_escalation)

# ✅ Condition for Human Escalation
def route_chat(state: ChatState):
    if state["category"] == "escalation":
        return "human_escalation"
    return END

graph.set_entry_point("generate_response")
graph.add_conditional_edges("generate_response", route_chat)
graph.add_edge("human_escalation", END)

# ✅ Compile AI Chatbot
chatbot_graph = graph.compile()