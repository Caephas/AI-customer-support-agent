from fastapi import APIRouter
# from app.services.crm import get_customer_data

router = APIRouter()

@router.get("/customers/{customer_id}")
def get_customer(customer_id: str):
    return 'get_customer_data'(customer_id)