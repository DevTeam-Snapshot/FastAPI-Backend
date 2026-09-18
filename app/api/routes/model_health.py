# 모델 서버 상태 확인 API

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.clients.draft_image import (
    DraftImageClientError,
)
from app.clients.grpc_draft_image import (
    draft_image_client,
)
from app.clients.planning_agent import (
    PlanningAgentClientError,
    planning_agent_client,
)


router = APIRouter(
    prefix="/api/model",
    tags=["model"],
)


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
)
async def check_model_health() -> dict[str, bool]:
    try:
        planning_agent_healthy = (
            await planning_agent_client.health_check()
        )
        draft_image_healthy = (
            await draft_image_client.health_check()
        )

    except (
        PlanningAgentClientError,
        DraftImageClientError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "reason": error.reason,
                "message": error.message,
                "retryable": error.retryable,
            },
        ) from error

    if (
        not planning_agent_healthy
        or not draft_image_healthy
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "V2 모델 서비스가 준비되지 않았습니다."
            ),
        )

    return {
        "healthy": True,
        "planning_agent": planning_agent_healthy,
        "draft_image": draft_image_healthy,
    }