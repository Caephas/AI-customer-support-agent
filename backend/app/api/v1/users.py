from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def list_users():
    return 'get_all_users'()