from fastapi import APIRouter

# health.py 서버 상태 라우터
from app.api.routes.health import router as health_router

# 모델 서버 상태 확인 라우터
from app.api.routes.model_health import router as model_health_router

# DB 저장 라우터 등록
from app.api.routes.test_items import router as test_items_router

# 테스트 라우터 등록
from app.api.routes.integration import router as integration_router



api_router = APIRouter()

# 서버 상태 확인 라우터
api_router.include_router(health_router)

# 모델 서버 상태 확인 라우터
api_router.include_router(model_health_router)

# DB 저장 라우터
api_router.include_router(test_items_router)

# 테스트 전용 라우터
api_router.include_router(integration_router)