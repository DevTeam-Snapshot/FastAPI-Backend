from fastapi import APIRouter

# health.py 서버 상태 라우터
from app.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)