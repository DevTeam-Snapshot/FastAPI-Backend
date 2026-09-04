from fastapi import FastAPI
from app.api.router import api_router

app = FastAPI(
    title = "Snapshot Backend API",
    description = "숙박업 소상공인을 위한 생성형 AI 광고 제작 서비스",
    version = "0.1.0"
)

# router.py의 기능 가져오기
app.include_router(api_router)