from fastapi import APIRouter, HTTPException, status

from app.clients.model import model_client


# 모델 서버 상태 확인 API
router = APIRouter(
    prefix="/api/model",
    tags=["Model"]
)


# FastAPI에서 이미지 모델 서버 연결 상태 확인
@router.get(
    "/health",
    status_code=status.HTTP_200_OK
)
async def check_model_health() -> dict[str, bool]:
    try:
        # 이미지 모델의 HealthCheck RPC 호출
        healthy = await model_client.health_check()

    except ConnectionError as error:
        # 모델 서버에 연결할 수 없으면 HTTP 503 반환
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error)
        ) from error

    # 서버는 연결됐지만 healthy가 false인 경우
    if not healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="이미지 모델 서버가 준비되지 않았습니다."
        )

    return {
        "healthy": True
    }