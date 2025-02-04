from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.core.firebase import create_user,get_user, delete_user
from backend.app.core.security import create_access_token

router = APIRouter()

class UserSignup(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    uid: str


@router.post("/signup")
def signup(user: UserSignup):
    try:
        firebase_user = create_user(user.email, user.password)
        return {"message": "User created", "uid": firebase_user.uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(request: LoginRequest):
    """Generates JWT token for a Firebase user"""
    try:
        user = get_user(request.uid)  # Verify user exists in Firebase
        token = create_access_token({"sub": user.uid})
        return {"token": token, "uid": user.uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/user/{uid}")
def get_user_info(uid: str):
    try:
        user = get_user(uid)
        return {"uid": user.uid, "email": user.email}
    except Exception as e:
        raise HTTPException(status_code=404, detail="User not found")

@router.delete("/user/{uid}")
def remove_user(uid: str):
    try:
        delete_user(uid)
        return {"message": "User deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))