# A·B·C 광고 초안 API의 요청·응답 형식

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    AdvertisementDraftStatus,
    DraftDirection,
)

# 광고 초안 응답 형식
class AdvertisementDraftResponse(BaseModel):
    id : UUID
    session_id: UUID

    generation_round: int                       # 1: 최소 생성, 2: 재생성
    direction: DraftDirection                   # 객실 중심, 감성 중심, 혜택 중심 중 1
    status: AdvertisementDraftStatus            # 초안 생성 상태

    image_url: str | None                       # 이미지 URL
    mime_type: str                              # 이미지 확장자
    file_size: int | None                       # 이미지 크기

    is_selected: bool                           # 선택된 초안인가?

    error_code: str | None                      # 오류 코드
    error_message: str | None                   # 오류 메시지

    created_at: datetime                        # 초안 생성 시간
    updated_at: datetime                        # 업데이트 시간
    completed_at: datetime | None               # 완료된 시간

    # SQLAlchemy 모델을 Pydantic 응답으로 변환
    model_config = ConfigDict(from_attributes=True)

# 한 기획 세션의 전체 광고 초안 목록
class AdvertisementDraftListResponse(BaseModel):
    session_id: UUID

    # 2차 재생성 기회를 썼는지 여부
    regeneration_used: bool

    # 1차와 2차 초안 목록
    drafts: list[AdvertisementDraftResponse]