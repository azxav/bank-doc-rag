"""Aggregate v1 routers."""

from fastapi import APIRouter

from app.api.v1.ask import router as ask_router
from app.api.v1.auth import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(ask_router)
