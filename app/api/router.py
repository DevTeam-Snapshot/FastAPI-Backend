from fastapi import APIRouter

# health.py 서버 상태 라우터
from app.api.routes.health import router as health_router

# 모델 서버 상태 확인 라우터
from app.api.routes.model_health import router as model_health_router

# 이미지 생성 요청 라우터
from app.api.routes.image_generations import router as image_generations_router

# 광고 기획 세션 라우터
from app.api.routes.planning_sessions import router as planning_sessions_router

# 광고 초안 생성 및 조회 라우터
from app.api.routes.advertisement_drafts import router as advertisement_drafts_router

# 광고 기획 대화 라우터
from app.api.routes.planning_turns import (
    router as planning_turns_router,
)

# 광고 초안 이미지 다운로드 라우터
from app.api.routes.draft_downloads import (
    router as draft_downloads_router,
)

api_router = APIRouter()

# 서버 상태 확인 라우터
api_router.include_router(health_router)

# 모델 서버 상태 확인 라우터
api_router.include_router(model_health_router)

# 이미지 생성 요청 라우터
api_router.include_router(image_generations_router)

# 광고 기획 세션 생성 및 조회 라우터
api_router.include_router(planning_sessions_router)

# 광고 초안 생성 및 조회 라우터
api_router.include_router(advertisement_drafts_router)

# 광고 초안 이미지 다운로드
api_router.include_router(draft_downloads_router)

# 광고 기획 대화 라우터
api_router.include_router(planning_turns_router)