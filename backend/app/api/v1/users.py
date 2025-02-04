from fastapi import APIRouter
# from app.services.users import get_all_users

router = APIRouter()

@router.get("/")
def list_users():
    return 'get_all_users'()