from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    String,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import PlanningSessionStatus

# 하나의 광고 기획 과정과 최종 기획서, 원본 이미지를 관리
class PlanningSession(Base):
    __tablename__ = "planning_sessions"

    # 광고 기획 세션 식별자
    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # 광고 기획의 전체 진행 상태
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PlanningSessionStatus.PLANNING.value,
        server_default=PlanningSessionStatus.PLANNING.value,
        index=True,
    )

    # 호텔, 모텔, 리조트, 펜션, 기타 중 하나
    lodging_type: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    # lodging_type이 other(기타)인 경우 실제 숙소 유형
    lodging_type_detail: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # 숙소 이름
    lodging_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # 숙소 위치
    location: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    # 객실 내외부 특징
    selling_points: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # 숙소에서 제공하는 서비스와 혜택
    lodging_service: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # 광고 분위기
    mood: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # 선호 색상 또는 모델에게 위임하는 auto
    color_preference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # 광고 대상
    target_audience: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # 최종 확정된 광고 문구
    ad_copy: Mapped[str | None] = mapped_column(
        String(60),
        nullable=True,
    )

    # 사용자가 업로드한 원본 파일명
    original_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # 서버에 저장된 원본 이미지 URL
    original_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # 원본 이미지의 MIME 타입
    original_mime_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # 원본 이미지의 byte 크기
    original_file_size: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    # 사용자가 다시 생성 기회를 성공적으로 사용했는지 여부
    regeneration_used: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # 세션 생성 시각
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # 최근 수정 시각
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # 사용자가 기획서를 최종 확인한 시각
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )