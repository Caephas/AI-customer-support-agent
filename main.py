from fastapi import FastAPI
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.crm import router as crm_router
from backend.app.api.v1.users import router as users_router
from backend.app.api.v1.notifications import router as  notifications_router
from backend.app.api.v1.webhooks import router as webhooks_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI-Powered Customer Support Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Use ["http://localhost:5173"] for stricter security
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(crm_router, prefix="/api/v1/crm", tags=["CRM"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(webhooks_router, prefix='/api/v1/webhooks', tags=['Webhooks'])
@app.get("/")
async def root():
    return {"message": "AI Customer Support API is running"}