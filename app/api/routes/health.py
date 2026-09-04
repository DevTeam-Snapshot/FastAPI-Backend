from fastapi import APIRouter

# FastAPI 상태 확인 라우터
router = APIRouter(tags = ["Health Check"])

# 서버 상태 확인
@router.get("/health")
def health_check():
    return {"status" : "ok"}