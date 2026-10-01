# 완성된 광고 초안 이미지 다운로드 API

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import AdvertisementDraftStatus
from app.services.advertisement_draft_service import (
    advertisement_draft_service,
)
from app.services.image_storage import image_storage


router = APIRouter(
    prefix="/api/drafts",
    tags=["advertisement-drafts"],
)


@router.get(
    "/{draft_id}/download",
    response_class=FileResponse,
)
def download_draft_image(
    draft_id: UUID,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
) -> FileResponse:
    # draft_id에 해당하는 광고 초안 조회
    try:
        draft = advertisement_draft_service.get_draft_by_id(
            db=db,
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

    # 생성이 완료된 초안만 다운로드 가능
    if (
        draft.status
        != AdvertisementDraftStatus.COMPLETED.value
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="생성이 완료된 광고 초안만 다운로드할 수 있습니다.",
        )

    if draft.image_url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="광고 초안의 이미지 정보가 없습니다.",
        )

    # 서버에 저장된 실제 PNG 파일 조회
    try:
        file_path = image_storage.get_generated_path(
            draft.id
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    # Content-Disposition: attachment 응답 (저장되는 파일 형식, 이름)
    return FileResponse(
        path=file_path,
        media_type="image/png",
        filename=f"Snapshot_{draft.direction}.png",
    )