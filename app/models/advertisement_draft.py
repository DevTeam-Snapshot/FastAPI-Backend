from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AdvertisementDraftStatus


# A·B·C 광고 초안과 생성 결과를 관리
class AdvertisementDraft(Base):
    __tablename__ = "advertisement_drafts"

    # 동일한 세션과 회차에 같은 방향의 초안이 중복 생성되는 것을 방지
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "generation_round",
            "direction",
            name="uq_advertisement_drafts_session_round_direction",
        ),
    )

    # 광고 초안 식별자
    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # 초안이 소속된 광고 기획 세션
    session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "planning_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # 최초 생성은 1, 사용자 다시 생성은 2
    generation_round: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    # room, emotion, benefit 중 하나
    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # 개별 초안의 생성 진행 상태
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AdvertisementDraftStatus.PENDING.value,
        server_default=AdvertisementDraftStatus.PENDING.value,
        index=True,
    )

    # 서버에 저장된 결과 PNG URL
    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # 생성 결과 이미지의 MIME 타입
    mime_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="image/png",
        server_default="image/png",
    )

    # 생성 결과 이미지의 byte 크기
    file_size: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    # 사용자가 최종 선택한 초안인지 여부
    is_selected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # 모델 또는 서버에서 반환한 내부 오류 코드
    error_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # 이미지 생성 실패 내용
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # 초안 생성 요청 시각
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

    # 초안 생성 완료 시각
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )