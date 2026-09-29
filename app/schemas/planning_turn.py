# React와 FastAPI 사이의 V2 기획 대화 요청·응답 형식

from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.models.enums import (
    AnswerStatus,
    BriefField,
    ConversationRole,
    LodgingType,
    MessageIntent,
    PlanningStep,
)


SellingPoint = Annotated[
    str,
    Field(min_length=1, max_length=100),
]

LodgingService = Annotated[
    str,
    Field(min_length=1, max_length=100),
]

# React가 관리하는 현재 임시 광고 기획서
class PlanningBrief(BaseModel):
    lodging_type: LodgingType | None = None
    lodging_type_detail: str | None = Field(
        default=None,
        max_length=50,
    )
    lodging_name: str | None = Field(
        default=None,
        max_length=100,
    )
    location: str | None = Field(
        default=None,
        max_length=200,
    )
    selling_points: list[SellingPoint] = Field(
        default_factory=list,
        max_length=5,
    )
    lodging_service: list[LodgingService] = Field(
        default_factory=list,
        max_length=5,
    )
    mood: str | None = Field(
        default=None,
        max_length=100,
    )
    color_preference: str | None = Field(
        default=None,
        max_length=100,
    )
    target_audience: str | None = Field(
        default=None,
        max_length=100,
    )
    ad_copy: str | None = Field(
        default=None,
        max_length=60,
    )

    # 입력된 문자열의 앞뒤 공백 제거
    @field_validator(
        "lodging_type_detail",
        "lodging_name",
        "location",
        "target_audience",
        "mood",
        "color_preference",
        "ad_copy",
    )
    @classmethod
    def strip_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return value.strip() or None

    # 객실 내외부 특징의 앞뒤 공백 제거
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

    # 숙소 서비스·혜택의 앞뒤 공백 제거
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

    model_config = ConfigDict(extra="forbid")

# 모델이 대화 문맥으로 참고할 최근 메시지
class ConversationMessage(BaseModel):
    role: ConversationRole
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "대화 내용에는 공백만 입력할 수 없습니다."
            )

        return cleaned_value

    model_config = ConfigDict(extra="forbid")


# 한 번의 사용자 답변을 모델에 전달하는 REST 요청
class PlanningTurnRequest(BaseModel):
    user_message: str = Field(min_length = 1)
    current_step: PlanningStep
    brief: PlanningBrief

    conversation_history: list[
        ConversationMessage
    ] = Field(
        default_factory=list,
        max_length=12,
    )

    # 사용자 메시지 규칙 검사
    @field_validator("user_message")
    @classmethod
    def strip_user_message(
        cls,
        value: str
    ) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "사용자의 메시지가 필요합니다."
            )

        return cleaned_value

    model_config = ConfigDict(extra="forbid")


# 모델이 보내는 부분 변경값
BriefPatchValue = str | list[str] | None


# 한 번의 기획 대화 결과
class PlanningTurnResponse(BaseModel):
    request_id: str                     # 요청 번호
    session_id: str                     # 세션 ID UUID

    message_intent: MessageIntent
    answer_status: AnswerStatus         # 답변 상태
    assistant_message: str              # 질문

    # 응답에 포함된 필드만 React의 임시 기획서에 반영
    brief_updates: dict[str, BriefPatchValue]

    corrected_fields: list[BriefField]
    completed_fields: list[BriefField]
    missing_fields: list[BriefField]

    current_step: PlanningStep
    next_step: PlanningStep

    is_complete: bool

    model_config = ConfigDict(extra="forbid")
