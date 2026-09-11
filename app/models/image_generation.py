from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# 이미지 생성 요청/처리 결과를 담을 테이블 생성
class ImageGeneration(Base):
    __tablename__ = "image_generations"

    # 고유 요청 id
    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid = True),
        primary_key = True,
        default = uuid4
    )

        # 광고에 반영할 호텔 설명
    hotel_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # 이미지에 포함할 광고 문구
    ad_copy: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # 사용자가 입력한 선택 추가 지시
    additional_instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # 사용자가 업로드한 파일의 이름
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # 업로드한 원본 이미지 URL
    original_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # 모델이 생성한 결과 이미지 URL
    generated_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # 모델에게 전달받은 이미지 상태
    status: Mapped[str] = mapped_column(
        String(20),
        nullable = False,
        default="pending",
        server_default="pending",
        index = True
    )

    # 이미지 생성 실패 원인
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # 요청 생성 시각
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # 마지막 변경 시각
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )