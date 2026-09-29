from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import (
    LodgingType,
    PlanningSessionStatus,
)

# 객실 내외부 특징 입력 규칙
SellingPoint = Annotated[
    str,
    Field(min_length=1, max_length=100)
]

# 숙소 서비스 혜택 입력 규칙
LodgingService = Annotated[
    str,
    Field(min_length=1, max_length=100),
]

# 기획 세션 완료 후 전달하는 최종 광고 기획서
class PlanningSessionConfirmRequest(BaseModel):
    lodging_type: LodgingType

    lodging_type_detail: str | None = Field(
        default=None,
        max_length=50,
    )

    lodging_name: str = Field(
        min_length=1,
        max_length=100,
    )

    location: str = Field(
        min_length=1,
        max_length=200,
    )

    selling_points: list[SellingPoint] = Field(
        min_length=1,
        max_length=5
    )

    lodging_service: list[LodgingService] = Field(
        min_length=1,
        max_length=5,
    )

    mood: str = Field(
        min_length=1,
        max_length=100,
    )

    color_preference: str = Field(
        min_length=1,
        max_length=100,
    )

    target_audience: str = Field(
        min_length=1,
        max_length=100,
    )

    ad_copy: str = Field(
        min_length=1,
        max_length=60,
    )

    # 필수 문자열 앞뒤의 불필요한 공백 제거
    @field_validator(
        "lodging_name",
        "location",
        "target_audience",
        "mood",
        "color_preference",
        "ad_copy",
    )
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("공백만 입력할 수 없습니다.")

        return cleaned_value

    # 기타 숙소 유형 세부값 정리
    @field_validator("lodging_type_detail")
    @classmethod
    def strip_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return value.strip() or None

    # 매력 포인트 각 항목의 공백 제거
    @field_validator("selling_points")
    @classmethod
    def strip_selling_points(
        cls,
        values: list[str],
    ) -> list[str]:
        cleaned_values = [
            value.strip()
            for value in values
        ]

        if any(not value for value in cleaned_values):
            raise ValueError(
                "매력 포인트에는 공백만 입력할 수 없습니다."
            )

        return cleaned_values

    # 숙소 서비스·혜택 각 항목의 공백 제거
    @field_validator("lodging_service")
    @classmethod
    def strip_lodging_service(
        cls,
        values: list[str],
    ) -> list[str]:
        cleaned_values = [
            value.strip()
            for value in values
        ]

        if any(not value for value in cleaned_values):
            raise ValueError(
                "숙소 서비스에는 공백만 입력할 수 없습니다."
            )

        return cleaned_values

    # other 선택 시에만 세부 숙소 유형 필수
    @model_validator(mode="after")
    def validate_lodging_type_detail(
        self,
    ) -> "PlanningSessionConfirmRequest":
        if (
            self.lodging_type == LodgingType.OTHER
            and self.lodging_type_detail is None
        ):
            raise ValueError(
                "기타 숙소 유형을 입력해야 합니다."
            )

        # 기타가 아니라면 불필요한 세부값 제거
        if self.lodging_type != LodgingType.OTHER:
            self.lodging_type_detail = None

        return self

    # 정의하지 않은 필드가 들어오면 오타로 판단
    model_config = ConfigDict(extra="forbid")


# 광고 기획 세션 및 조회 API 형식
class PlanningSessionResponse(BaseModel):
    id: UUID
    status: PlanningSessionStatus

    lodging_type: LodgingType | None    # 숙소 유형
    lodging_type_detail: str | None     # 기타 숙소 유형
    lodging_name: str | None            # 숙소 이름
    location: str | None                # 숙소 위치
    selling_points: list[str] | None    # 숙소 객실 내외부 특징
    lodging_service: list[str] | None   # 숙소 서비스 및 혜택
    mood: str | None                    # 홍보물 분위기
    color_preference: str | None        # 선호하는 색상
    target_audience: str | None         # 홍보 타겟
    ad_copy: str | None                 # 광고 문구

    original_filename: str | None       # 원본 이미지 이름
    original_image_url: str | None      # 원본 이미지 URL
    original_mime_type: str | None      # 원본 이미지 타입
    original_file_size: int | None      # 원본 이미지 크기

    regeneration_used: bool             # 재생성 여부

    created_at: datetime                # 최초 생성 시간
    updated_at: datetime                # 업데이트된 시간
    confirmed_at: datetime | None       # 기획서 최종 확인 시간

    # SQLAlchemy -> Pydantic 응답으로 변환
    model_config = ConfigDict(from_attributes=True)
