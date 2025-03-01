# AI-Powered Customer Support Agent 🚀

A FastAPI-based AI chatbot with RAG (Retrieval-Augmented Generation), Pinecone vector search, Firebase authentication, Celery task queue, and Redis caching.

📌 Features

✅ AI Chatbot powered by OpenAI 
✅ Retrieval-Augmented Generation (RAG) using Pinecone Vector Search
✅ User Authentication & Token Management with Firebase & JWT
✅ Background Processing using Celery & Redis
✅ Categorization & Routing (Billing, Technical, General, Escalation)
✅ Salesforce & Slack Integration for ticketing and escalation
✅ Dockerized for Deployment with Docker Compose & Kubernetes support

```
📂 Project Structure

customer-support-agent/
│── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI endpoints
│   │   ├── core/                # Firebase authentication & security
│   │   ├── integrations/        # Salesforce, Slack, and third-party integrations
│   │   ├── models/              # Database models and schemas
│   │   ├── services/            # AI processing, Celery tasks, and Pinecone setup
│   │   ├── utils/               # Utility functions
│   │   ├── db.py                # Firestore database connection
│   │   ├── main.py              # FastAPI entry point
│   │── tests/                   # Unit and integration tests
│── deployment/
│   ├── aws/                     # AWS deployment setup
│   ├── gcp/                     # GCP deployment setup
│── infrastructure/
│   ├── k8s/                     # Kubernetes manifests
│   ├── docker-compose.yml        # Docker Compose setup
│── logs/                         # Logs storage
│── .env                          # Environment variables
│── Dockerfile                     # Docker image configuration
│── requirements.txt               # Dependencies list
│── pyproject.toml                 # Poetry package management
│── README.md                      # Documentation
```

```
🚀 Getting Started

1️⃣ Prerequisites
 • Python 3.10+
 • Docker & Docker Compose
 • Poetry (Python package manager)
 • Redis (for caching & task queue)
 • Firebase Admin SDK (for authentication)

2️⃣ Install Dependencies

poetry install

3️⃣ Set Up Environment Variables

Create a .env file:

SECRET_KEY=your_secret_key
FIREBASE_CREDENTIALS=path_to_your_firebase_credentials.json
PINECONE_API_KEY=your_pinecone_api_key

4️⃣ Start Redis & Celery

redis-server &
celery -A backend.app.services.chat.celery_app worker --loglevel=info

5️⃣ Run the FastAPI Server

poetry run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

6️⃣ Run with Docker

docker-compose up --build
```

```
🛠 API Endpoints

Authentication

Method Endpoint Description
POST /api/v1/auth/signup User signup
POST /api/v1/auth/login Login & get JWT token
POST /api/v1/auth/logout Logout (blacklist token)
GET /api/v1/auth/user/{uid} Get user info

Chatbot API

Method Endpoint Description
POST /api/v1/chat/query Send a message to AI
GET /api/v1/chat/query/status/{task_id} Check chat task status
POST /api/v1/chat/save Save a chat manually

CRM (Salesforce) API

Method Endpoint Description
POST /api/v1/crm/create_ticket Create a support ticket
```

💡 Future Enhancements

🔹 Implement real-time WebSocket support for instant AI responses
🔹 Improve query classification with fine-tuned LLM models
🔹 Add a feedback loop for model improvement

📝 License

This project is MIT Licensed. Feel free to use, modify, and distribute it.
