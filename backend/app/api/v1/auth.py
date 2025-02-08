from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from backend.app.core.firebase import create_user, get_user, delete_user
from backend.app.core.security import create_access_token, blacklist_token, verify_token

router = APIRouter()

class UserSignup(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    uid: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

@router.post("/signup")
def signup(user: UserSignup):
    """Creates a new user in Firebase."""
    try:
        firebase_user = create_user(user.email, user.password)
        return {"message": "User created", "uid": firebase_user.uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(request: LoginRequest):
    """Generates JWT token for a Firebase user."""
    try:
        user = get_user(request.uid)  # Verify user exists in Firebase
        token = create_access_token({"sub": user.uid})
        return {"token": token, "uid": user.uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/user/{uid}")
def get_user_info(uid: str):
    """Fetches user information."""
    try:
        user = get_user(uid)
        return {"uid": user.uid, "email": user.email}
    except Exception as e:
        raise HTTPException(status_code=404, detail="User not found")

@router.delete("/user/{uid}")
def remove_user(uid: str):
    """Deletes a user."""
    try:
        delete_user(uid)
        return {"message": "User deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    """Logs out user by blacklisting their token."""
    blacklist_token(token)
    return {"message": "Successfully logged out"}

@router.get("/protected")
def protected_route(user: dict = Depends(verify_token)):
    """Example of a protected route that requires authentication."""
    return {"message": "You have access!", "user": user}