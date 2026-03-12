"""Main API router – aggregates all sub-routers."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.calendar import router as calendar_router
from app.api.chat import router as chat_router
from app.api.analytics import router as analytics_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(calendar_router, prefix="/calendar", tags=["calendar"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
