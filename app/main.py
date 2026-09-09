from fastapi import FastAPI
import os
from app.api.router import api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title = "Snapshot Backend API",
    description = "숙박업 소상공인을 위한 생성형 AI 광고 제작 서비스",
    version = "0.1.0"
)

# 로컬에서 실행되는 React 개발 서버 주소 허용
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# 위 허용된 프론트엔드 주소에서 API 호출 가능하도록 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins = allowed_origins,
    allow_credentials = True,
    allow_methods= ["*"],
    allow_headers= ["*"]
)

# router.py의 기능 가져오기
app.include_router(api_router)
