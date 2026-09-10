from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# 이미지 생성 요청 처리 상태
class ImageGenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# 이미지 생성 요청 응답 형식
class ImageGenerationResponse(BaseModel):
    id: UUID
    hotel_description: str
    ad_copy: str
    additional_instructions: str | None
    original_filename: str
    original_image_url: str | None
    generated_image_url: str | None
    status: ImageGenerationStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    # SQLAlchemy 객체의 속성을 읽어 Pydantic 응답으로 변환
    model_config = ConfigDict(from_attributes=True)
