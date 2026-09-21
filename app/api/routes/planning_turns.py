# V2 광고 기획 대화 API

from typing import Annotated
from uuid import UUID
import grpc

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.clients.planning_agent import (
    PlanningAgentClientError,
    planning_agent_client,
)
from app.db.session import get_db
from app.models.enums import (
    PlanningSessionStatus
)

from app.schemas.planning_turn import (
    PlanningTurnRequest,
    PlanningTurnResponse,
)
from app.services.image_storage import image_storage
from app.services.planning_session_service import (
    planning_session_service,
)

# gRPC 모델 오류를 REST HTTP 상태로 변환
def get_model_error_http_status(
    error: PlanningAgentClientError,
) -> int:
    # 입력 이미지나 메시지 크기 초과
    if error.reason == "INPUT_TOO_LARGE":
        return status.HTTP_413_CONTENT_TOO_LARGE

    grpc_status_mapping = {
        grpc.StatusCode.INVALID_ARGUMENT: (
            status.HTTP_422_UNPROCESSABLE_CONTENT
        ),
        grpc.StatusCode.FAILED_PRECONDITION: (
            status.HTTP_409_CONFLICT
        ),
        grpc.StatusCode.RESOURCE_EXHAUSTED: (
            status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        grpc.StatusCode.UNAVAILABLE: (
            status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        grpc.StatusCode.DEADLINE_EXCEEDED: (
            status.HTTP_504_GATEWAY_TIMEOUT
        ),
        grpc.StatusCode.INTERNAL: (
            status.HTTP_502_BAD_GATEWAY
        ),
        grpc.StatusCode.CANCELLED: (
            status.HTTP_503_SERVICE_UNAVAILABLE
        ),
    }

    return grpc_status_mapping.get(
        error.grpc_code,
        status.HTTP_502_BAD_GATEWAY,
    )

router = APIRouter(
    prefix="/api/planning-sessions",
    tags=["planning-turns"],
)


# 사용자 답변을 모델에 전달하고 다음 질문을 받는 API
@router.post(
    "/{session_id}/turns",
    response_model=PlanningTurnResponse,
)
async def process_planning_turn(
    session_id: UUID,
    request: PlanningTurnRequest,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
) -> PlanningTurnResponse:
    try:
        planning_session = (
            planning_session_service.get_session(
                db=db,
                session_id=session_id,
            )
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=str(error),
        ) from error

    if planning_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="광고 기획 세션을 찾을 수 없습니다.",
        )

    # 확정된 기획서는 대화로 수정하지 않음
    if (
        planning_session.status
        != PlanningSessionStatus.PLANNING.value
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "기획이 완료된 세션에서는 "
                "대화를 진행할 수 없습니다."
            ),
        )

    # React 값이 아니라 DB 기록과 실제 파일을 함께 확인
    original_image_uploaded = (
        planning_session.original_image_url
        is not None
        and image_storage.has_original(
            planning_session.id
        )
    )

    try:
        return await planning_agent_client.process_turn(
            session_id=planning_session.id,
            request=request,
            original_image_uploaded=(
                original_image_uploaded
            ),
        )

    except PlanningAgentClientError as error:
        raise HTTPException(
            status_code=(
                get_model_error_http_status(error)
            ),
            detail={
                "reason": error.reason,
                "message": error.message,
                "retryable": error.retryable,
                "request_id": error.request_id,
            },
        ) from error