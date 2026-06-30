from fastapi import APIRouter
from app.api import auth, books, reading, households

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(books.router)
api_router.include_router(reading.router)
api_router.include_router(households.router)
