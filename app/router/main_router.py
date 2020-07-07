from fastapi import APIRouter
from app.views import accounts


api_router = APIRouter()

api_router.include_router(accounts.router, tags=["login"])

