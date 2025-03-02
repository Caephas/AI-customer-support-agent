from datetime import datetime, timezone
from typing import TypedDict, List, Union
from openai import OpenAI
import os
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from celery import Celery
from backend.app.core.firebase import db
from backend.app.integrations.salesforce import create_salesforce_ticket
from backend.app.integrations.slack import send_slack_message
import time
import logging
from backend.app.services.vector_store_pinecone import get_pinecone_vectorstore

# Set up OpenAI API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define your model name for OpenAI
MODEL_NAME = "gpt-3.5-turbo"

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define AI Chatbot State
class ChatState(TypedDict):
    user_id: str
    chat_history: List[Union[HumanMessage, AIMessage]]
    response: str
    category: str  # billing, technical, general, escalation

# Initialize Celery Worker
celery_app = Celery(
    "tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=["backend.app.services.chat"]
)

celery_app.conf.update(
    task_track_started=True,
    result_backend="redis://redis:6379/0",
    result_extended=True,
    broker_connection_retry_on_startup=True,
)

# Format Messages for OpenAI API (same structure as before)
def format_message(message):
    """Formats messages for the OpenAI API."""
    if isinstance(message, SystemMessage):
        return {"role": "system", "content": message.content}
    elif isinstance(message, HumanMessage):
        return {"role": "user", "content": message.content}
    elif isinstance(message, AIMessage):
        return {"role": "assistant", "content": message.content}
    else:
        return {"role": "user", "content": str(message)}

# Query Classification Logic using OpenAI API
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
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": classification_prompt}]
    )
    return response.choices[0].message.content.strip().lower()

# Fetch Chat History
def fetch_chat_history(user_id: str) -> List[Union[HumanMessage, AIMessage]]:
    chats = (
        db.collection("chats")
        .where("user_id", "==", user_id)
        .order_by("timestamp", direction="DESCENDING")
        .limit(10)
        .stream()
    )
    return [
        HumanMessage(content=chat.to_dict()["message"]) if i % 2 == 0 
        else AIMessage(content=chat.to_dict()["response"])
        for i, chat in enumerate(chats)
    ]

# Check Cached Response
def check_cached_response(user_id: str, message: str) -> Union[str, None]:
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

    if occurrences == 0:
        return None

    if occurrences == 1:
        return f"You've asked this question before! Here's what I told you:\n\n{last_response}"

    return f"You've already asked this {occurrences} times! My previous response was:\n\n{last_response}"

# AI Response Generation using OpenAI API
def generate_response(state: ChatState) -> ChatState:
    """Generates AI response while tracking performance metrics."""
    start_time = time.time()  # Start timer

    # Fetch recent chat history
    history = fetch_chat_history(state["user_id"])

    # Convert last message to HumanMessage (if needed)
    last_message_data = state["chat_history"][-1]
    last_message = (
        HumanMessage(content=last_message_data["content"])
        if isinstance(last_message_data, dict)
        else last_message_data
    )

    messages = [SystemMessage(content="You are a helpful support assistant.")]
    messages.extend(history)
    messages.append(last_message)

    # Step 1: Check if the answer is in chat history
    for past_msg in history:
        if last_message.content.lower() in past_msg.content.lower():
            logging.info("Cache Hit: Returning response from chat history.")
            return {
                "user_id": state["user_id"],
                "chat_history": state["chat_history"],
                "response": past_msg.content,
                "category": classify_query(last_message.content),
            }

    # Step 2: Retrieve relevant documents from Pinecone
    pinecone_start = time.time()
    retrieved_docs = retrieve_documents(last_message.content)
    pinecone_time = round(time.time() - pinecone_start, 2)
    logging.info(f"Pinecone Query Time: {pinecone_time}s | Documents Retrieved: {len(retrieved_docs)}")

    # Step 3: Remove duplicate documents
    unique_docs = list(set(retrieved_docs))
    knowledge_context = "\n".join(unique_docs)

    if unique_docs:
        messages.append(SystemMessage(content=f"Relevant knowledge:\n{knowledge_context}"))

    # Step 4: Call OpenAI API for AI Response
    logging.info(f"AI Model Input: {messages}")
    ai_start = time.time()
    ai_response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[format_message(m) for m in messages]
    )
    ai_time = round(time.time() - ai_start, 2)

    # Step 5: Handle AI response
    response_text = ai_response.choices[0].message.content if ai_response.choices else "No response generated"

    if not response_text.strip():
        logging.warning("AI returned an empty response!")

    # Step 6: Categorize response
    category = classify_query(last_message.content)

    # Step 7: Log response time & performance metrics
    execution_time = round(time.time() - start_time, 2)
    logging.info(f"Total AI Processing Time: {execution_time}s | AI Time: {ai_time}s | Category: {category}")

    return {
        "user_id": state["user_id"],
        "chat_history": state["chat_history"],
        "response": response_text,
        "category": category,
    }

# Save Chat in Firestore
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
        print(f"Firestore Error: {e}")

# Process Chat Async
@celery_app.task(name='tasks')
def process_chat_async(user_id: str, message: str):
    """Handles chat requests asynchronously using Celery."""
    # Check cache before processing
    cached_response = check_cached_response(user_id, message)
    if cached_response:
        return {
            "user_id": user_id,
            "chat_history": [{"role": "user", "content": message}],
            "response": cached_response,
            "category": "cached"
        }

    # Prepare chat state
    chat_state = {
        "user_id": user_id,
        "chat_history": [{"role": "user", "content": message}],
        "response": "",
        "category": ""
    }

    # Generate AI Response
    response = generate_response(chat_state)

    # Save Chat History to Firestore (caching it)
    if response.get("response"):
        save_chat(user_id, message, response["response"], response.get("category", ""))

    return response

def retrieve_documents(query: str):
    """Fetch relevant knowledge base documents using Pinecone vector search."""
    vectorstore = get_pinecone_vectorstore()
    docs = vectorstore.similarity_search(query, k=3)
    return [doc.page_content for doc in docs]

# Define LangGraph Flow
graph = StateGraph(ChatState)
graph.add_node("generate_response", generate_response)
graph.set_entry_point("generate_response")
graph.add_edge("generate_response", END)
chatbot_graph = graph.compile()