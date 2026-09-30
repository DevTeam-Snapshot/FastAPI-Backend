# A·B·C 광고 초안 생성 및 조회 API

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.advertisement_draft import AdvertisementDraft
from app.models.enums import PlanningSessionStatus
from app.schemas.advertisement_draft import (
    AdvertisementDraftListResponse,
    AdvertisementDraftResponse,
)
from app.services.advertisement_draft_service import (
    DraftRegenerationError,
    DraftRoundAlreadyExistsError,
    DraftSelectionError,
    advertisement_draft_service
)

from app.services.draft_generation_service import (
    draft_generation_service,
)

from app.services.planning_session_service import (
    planning_session_service
)

# 기획 세션 기반 광고 초안 API
router = APIRouter(
    prefix = "/api/planning-sessions/{session_id}",
    tags = ["advertisement-drafts"]
)

# 3가지 초안 레코드 생성
@router.post(
    "/draft-generations",
    response_model=AdvertisementDraftListResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_initial_drafts(
    session_id: UUID,
    db: Annotated[
        Session,
        Depends(get_db)
    ]
)-> AdvertisementDraftListResponse:
    # 초안 생성을 위한 기획 세션 조회
    try:
        planning_session = planning_session_service.get_session(
            db = db,
            session_id = session_id
        )

        if planning_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="광고 기획 세션을 찾을 수 없습니다.",
            )

    except RuntimeError as error:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = str(error)
        ) from error

    # confirmed: 최초 초안 생성
    # generating: 모델 오류로 실패한 1회차 초안 재시도
    allowed_statuses = {
        PlanningSessionStatus.CONFIRMED.value,
        PlanningSessionStatus.GENERATING.value,
    }

    if planning_session.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "확정된 기획 세션 또는 최초 생성에 실패한 "
                "세션에서만 광고 초안을 생성할 수 있습니다."
            ),
        )

    try:
        drafts = advertisement_draft_service.create_initial_drafts(
            db = db,
            planning_session = planning_session
        )

    # 초안을 이미 생성한 경우
    except DraftRoundAlreadyExistsError as error:
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = str(error)
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = str(error)
        ) from error

    # A·B·C 초안을 생성하고 결과 저장
    try:
        drafts = await draft_generation_service.generate_drafts(
            db=db,
            planning_session=planning_session,
            drafts=drafts,
        )

    except (ValueError, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
    

    return AdvertisementDraftListResponse(
        session_id=planning_session.id,
        regeneration_used=planning_session.regeneration_used,
        drafts = drafts
    )

# A·B·C 광고 초안 3개 재생성 요청
@router.post(
    "/draft-generations/regenerate",
    response_model=AdvertisementDraftListResponse,
    status_code=status.HTTP_201_CREATED,
)
async def regenerate_drafts(
    session_id: UUID,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
) -> AdvertisementDraftListResponse:
    # 재생성할 기획 세션 조회
    try:
        planning_session = planning_session_service.get_session(
            db=db,
            session_id=session_id,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    if planning_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="광고 기획 세션을 찾을 수 없습니다.",
        )

    try:
        regeneration_drafts = (
            advertisement_draft_service.prepare_regeneration_drafts(
                db=db,
                planning_session=planning_session,
            )
        )

    except DraftRegenerationError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    # 2회차 A·B·C 초안을 생성하고 성공 여부 저장
    try:
        regeneration_drafts = (
            await draft_generation_service.generate_drafts(
                db=db,
                planning_session=planning_session,
                drafts=regeneration_drafts,
            )
        )

    except (ValueError, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    return AdvertisementDraftListResponse(
        session_id=planning_session.id,
        regeneration_used=planning_session.regeneration_used,
        drafts=regeneration_drafts,
    )

# 하나의 기획 세션의 모든 광고 초안 조회
@router.get(
    "/drafts",
    response_model=AdvertisementDraftListResponse
)
def read_drafts(
    session_id: UUID,
    db: Annotated[
        Session,
        Depends(get_db)
    ]
) -> AdvertisementDraftListResponse:
    try:
        planning_session = planning_session_service.get_session(
            db = db,
            session_id = session_id
        )

        # 해당 id 세션 조회가 되지 않을 때
        if planning_session is None:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "광고 기획 세션을 찾을 수 없습니다."
            )

        drafts = advertisement_draft_service.get_drafts(
            db = db,
            session_id = session_id
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = str(error)
        ) from error

    return AdvertisementDraftListResponse(
        session_id = planning_session.id,
        regeneration_used = planning_session.regeneration_used,
        drafts = drafts
    )

# 세션에 속한 광고 초안 한개 조회
@router.get(
    "/drafts/{draft_id}",
    response_model=AdvertisementDraftResponse
)
def read_draft(
    session_id: UUID,
    draft_id: UUID,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
) -> AdvertisementDraft:
    try:
        planning_session = planning_session_service.get_session(
            db=db,
            session_id=session_id,
        )

        if planning_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="광고 기획 세션을 찾을 수 없습니다.",
            )

        draft = advertisement_draft_service.get_draft(
            db=db,
            session_id=session_id,
            draft_id=draft_id,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    if draft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="광고 초안을 찾을 수 없습니다.",
        )

    return draft

# 완성된 광고 초안 한 개를 최종 선택 
@router.post(
    "/drafts/{draft_id}/select",
    response_model=AdvertisementDraftResponse,
    status_code=status.HTTP_200_OK
)
def select_advertisement_draft(
    session_id: UUID,
    draft_id: UUID,
    db: Annotated[
        Session,
        Depends(get_db)
    ]
) -> AdvertisementDraft:
    # 초안이 속한 기획 세션 조회
    try:
        planning_session = planning_session_service.get_session(
            db=db,
            session_id=session_id,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    if planning_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="광고 기획 세션을 찾을 수 없습니다.",
        )

    # 세션에 속한 초안 조회
    try:
        draft = advertisement_draft_service.get_draft(
            db=db,
            session_id=session_id,
            draft_id=draft_id,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    if draft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="광고 초안을 찾을 수 없습니다.",
        )

    # 완성된 초안 선택 결과 저장
    try:
        return advertisement_draft_service.select_draft(
            db=db,
            planning_session=planning_session,
            draft=draft,
        )

    except DraftSelectionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error