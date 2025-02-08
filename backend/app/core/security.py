from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import jwt
import os
from dotenv import load_dotenv
from firebase_admin import auth
import redis

load_dotenv()

# Load environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# OAuth2 scheme for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

class TokenData(BaseModel):
    uid: Optional[str] = None

# ✅ Initialize Redis (Ensure Redis is running)
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Generates a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def blacklist_token(token: str):
    """Blacklists a token in Redis using its expiry timestamp."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")

        if exp:
            ttl = int(exp - datetime.now(timezone.utc).timestamp())
            if ttl > 0:
                redis_client.setex(f"blacklist:{token}", ttl, "blacklisted")
    except jwt.ExpiredSignatureError:
        pass  # Token already expired, no need to blacklist
    except jwt.InvalidTokenError:
        pass  # Ignore if token is invalid

def is_token_blacklisted(token: str) -> bool:
    """Checks if a token is blacklisted in Redis."""
    return redis_client.exists(f"blacklist:{token}") == 1

def verify_token(token: str = Depends(oauth2_scheme)):
    """Verifies the token, ensures it's not expired, and checks if it's blacklisted."""
    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")

        if exp and datetime.now(timezone.utc).timestamp() > exp:
            raise HTTPException(status_code=401, detail="Token has expired")

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")