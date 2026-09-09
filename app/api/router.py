from fastapi import APIRouter

# health.py 서버 상태 라우터
from app.api.routes.health import router as health_router

# 모델 서버 상태 확인 라우터
from app.api.routes.model_health import router as model_health_router

api_router = APIRouter()

# 서버 상태 확인 라우터
api_router.include_router(health_router)

# 모델 서버 상태 확인 라우터
api_router.include_router(model_health_router)