# V2 광고 기획 대화 gRPC 클라이언트 -> 기획안을 모델 서버가 이해하는 형식으로 변환

from uuid import UUID, uuid4
from google.protobuf import empty_pb2

import grpc

from app.core.config import get_settings
from app.grpc_stubs import (
    hotel_ad_v2_pb2,
    hotel_ad_v2_pb2_grpc,
)
from app.models.enums import (
    AnswerStatus,
    BriefField,
    ConversationRole,
    LodgingType,
    MessageIntent,
    PlanningStep
)

from app.schemas.planning_turn import (
    PlanningBrief,
    PlanningTurnRequest,
    PlanningTurnResponse,
)

from app.clients.grpc_error import (
    get_safe_model_error_message,
    parse_model_rpc_error,
)


# 백엔드 Enum을 protobuf Enum으로 변환
LODGING_TYPE_TO_PROTO = {
    LodgingType.HOTEL: (
        hotel_ad_v2_pb2.LODGING_TYPE_HOTEL
    ),
    LodgingType.MOTEL: (
        hotel_ad_v2_pb2.LODGING_TYPE_MOTEL
    ),
    LodgingType.RESORT: (
        hotel_ad_v2_pb2.LODGING_TYPE_RESORT
    ),
    LodgingType.PENSION: (
        hotel_ad_v2_pb2.LODGING_TYPE_PENSION
    ),
    LodgingType.OTHER: (
        hotel_ad_v2_pb2.LODGING_TYPE_OTHER
    ),
}

PLANNING_STEP_TO_PROTO = {
    PlanningStep.LODGING_TYPE: (
        hotel_ad_v2_pb2.PLANNING_STEP_LODGING_TYPE
    ),
    PlanningStep.LODGING_INFORMATION: (
        hotel_ad_v2_pb2
        .PLANNING_STEP_LODGING_INFORMATION
    ),
    PlanningStep.SELLING_POINTS: (
        hotel_ad_v2_pb2.PLANNING_STEP_SELLING_POINTS
    ),
    PlanningStep.TARGET_AUDIENCE: (
        hotel_ad_v2_pb2.PLANNING_STEP_TARGET_AUDIENCE
    ),
    PlanningStep.MOOD: (
        hotel_ad_v2_pb2.PLANNING_STEP_MOOD
    ),
    PlanningStep.AD_COPY: (
        hotel_ad_v2_pb2.PLANNING_STEP_AD_COPY
    ),
    PlanningStep.COMPLETE: (
        hotel_ad_v2_pb2.PLANNING_STEP_COMPLETE
    ),
}

CONVERSATION_ROLE_TO_PROTO = {
    ConversationRole.USER: (
        hotel_ad_v2_pb2.CONVERSATION_ROLE_USER
    ),
    ConversationRole.ASSISTANT: (
        hotel_ad_v2_pb2.CONVERSATION_ROLE_ASSISTANT
    ),
}

BRIEF_FIELD_TO_PROTO = {
    BriefField.LODGING_TYPE: (
        hotel_ad_v2_pb2.BRIEF_FIELD_LODGING_TYPE
    ),
    BriefField.LODGING_TYPE_DETAIL: (
        hotel_ad_v2_pb2
        .BRIEF_FIELD_LODGING_TYPE_DETAIL
    ),
    BriefField.LODGING_NAME: (
        hotel_ad_v2_pb2.BRIEF_FIELD_LODGING_NAME
    ),
    BriefField.LOCATION: (
        hotel_ad_v2_pb2.BRIEF_FIELD_LOCATION
    ),
    BriefField.SELLING_POINTS: (
        hotel_ad_v2_pb2.BRIEF_FIELD_SELLING_POINTS
    ),
    BriefField.ORIGINAL_IMAGE: (
        hotel_ad_v2_pb2.BRIEF_FIELD_ORIGINAL_IMAGE
    ),
    BriefField.TARGET_AUDIENCE: (
        hotel_ad_v2_pb2.BRIEF_FIELD_TARGET_AUDIENCE
    ),
    BriefField.MOOD: (
        hotel_ad_v2_pb2.BRIEF_FIELD_MOOD
    ),
    BriefField.COLOR_PREFERENCE: (
        hotel_ad_v2_pb2.BRIEF_FIELD_COLOR_PREFERENCE
    ),
    BriefField.AD_COPY: (
        hotel_ad_v2_pb2.BRIEF_FIELD_AD_COPY
    ),
    }
    
PROTO_TO_LODGING_TYPE = {
    value: key
    for key, value in LODGING_TYPE_TO_PROTO.items()
    }

PROTO_TO_PLANNING_STEP = {
    value: key
    for key, value in PLANNING_STEP_TO_PROTO.items()
    }

PROTO_TO_BRIEF_FIELD = {
    value: key
    for key, value in BRIEF_FIELD_TO_PROTO.items()
    }

PROTO_TO_MESSAGE_INTENT = {
    hotel_ad_v2_pb2.MESSAGE_INTENT_ANSWER: (
        MessageIntent.ANSWER
    ),
    hotel_ad_v2_pb2.MESSAGE_INTENT_CORRECTION: (
        MessageIntent.CORRECTION
    ),
    hotel_ad_v2_pb2.MESSAGE_INTENT_QUESTION: (
        MessageIntent.QUESTION
    ),
    hotel_ad_v2_pb2.MESSAGE_INTENT_SYSTEM_EVENT: (
        MessageIntent.SYSTEM_EVENT
    ),
}

PROTO_TO_ANSWER_STATUS = {
    hotel_ad_v2_pb2.ANSWER_STATUS_VALID: (
        AnswerStatus.VALID
    ),
    hotel_ad_v2_pb2.ANSWER_STATUS_AMBIGUOUS: (
        AnswerStatus.AMBIGUOUS
    ),
    hotel_ad_v2_pb2.ANSWER_STATUS_OFF_TOPIC: (
        AnswerStatus.OFF_TOPIC
    ),
    hotel_ad_v2_pb2.ANSWER_STATUS_NOT_APPLICABLE: (
        AnswerStatus.NOT_APPLICABLE
    ),
}


class PlanningAgentClientError(RuntimeError):
    def __init__(
        self,
        reason: str,
        message: str,
        retryable: bool,
        grpc_code: grpc.StatusCode | None = None,
        request_id: str | None = None,
    ) -> None:
        self.reason = reason
        self.message = message
        self.retryable = retryable
        self.grpc_code = grpc_code
        self.request_id = request_id

        super().__init__(message)


class GrpcPlanningAgentClient:
    def __init__(
        self,
        grpc_target: str,
        timeout_seconds: float,
        max_message_size_mb: int,
    ) -> None:
        self.grpc_target = grpc_target
        self.timeout_seconds = timeout_seconds

        max_message_size = (
            max_message_size_mb
            * 1024
            * 1024
        )

        self.channel_options = [
            (
                "grpc.max_send_message_length",
                max_message_size,
            ),
            (
                "grpc.max_receive_message_length",
                max_message_size,
            ),
        ]
        
    # 광고 기획 대화 서비스 준비 상태 확인
    async def health_check(self) -> bool:
        try:
            async with grpc.aio.insecure_channel(
                self.grpc_target,
                options=self.channel_options,
            ) as channel:
                stub = (
                    hotel_ad_v2_pb2_grpc
                    .PlanningAgentServiceStub(channel)
                )

                response = await stub.HealthCheck(
                    empty_pb2.Empty(),
                    timeout=min(
                        self.timeout_seconds,
                        5.0,
                    ),
                )

        except grpc.aio.AioRpcError as error:
            parsed_error = parse_model_rpc_error(
                error=error,
            )

            raise PlanningAgentClientError(
                reason=parsed_error.reason,
                message=get_safe_model_error_message(
                    "광고 기획",
                    parsed_error,
                ),
                retryable=parsed_error.retryable,
                grpc_code=parsed_error.grpc_code,
                request_id=parsed_error.request_id,
            ) from error

        return response.healthy

    # React의 임시 기획서를 protobuf 메시지로 변환
    def build_proto_brief(
        self,
        brief: PlanningBrief,
    ) -> hotel_ad_v2_pb2.AdvertisementBrief:
        proto_brief = (
            hotel_ad_v2_pb2.AdvertisementBrief()
        )

        if brief.lodging_type is not None:
            proto_brief.lodging_type = (
                LODGING_TYPE_TO_PROTO[
                    brief.lodging_type
                ]
            )

        optional_text_fields = (
            "lodging_type_detail",
            "lodging_name",
            "location",
            "target_audience",
            "mood",
            "color_preference",
            "ad_copy",
        )

        for field_name in optional_text_fields:
            value = getattr(brief, field_name)

            if value is not None:
                setattr(
                    proto_brief,
                    field_name,
                    value,
                )

        proto_brief.selling_points.extend(
            brief.selling_points
        )

        return proto_brief

    # 한 번의 REST 대화 요청을 protobuf 요청으로 변환
    def build_proto_request(
        self,
        session_id: UUID,
        request: PlanningTurnRequest,
        original_image_uploaded: bool,
    ) -> hotel_ad_v2_pb2.ProcessTurnRequest:
        proto_request = (
            hotel_ad_v2_pb2.ProcessTurnRequest(
                request_id=str(uuid4()),
                session_id=str(session_id),

                # FastAPI에서만 기획단계 확인
                state_revision=0,
                event_type=(
                    hotel_ad_v2_pb2
                    .TURN_EVENT_TYPE_USER_MESSAGE
                ),
                user_message=request.user_message,
                current_step=PLANNING_STEP_TO_PROTO[
                    request.current_step
                ],
                original_image_uploaded=(
                    original_image_uploaded
                ),
            )
        )

        proto_request.brief.CopyFrom(
            self.build_proto_brief(
                request.brief
            )
        )

        for message in request.conversation_history:
            proto_message = (
                proto_request.conversation_history.add()
            )
            proto_message.role = (
                CONVERSATION_ROLE_TO_PROTO[
                    message.role
                ]
            )
            proto_message.content = message.content

        return proto_request

    # protobuf 기획서 변경값을 REST 응답 형식으로 변환
    def parse_brief_updates(
        self,
        patch: hotel_ad_v2_pb2.BriefPatch,
    ) -> dict[str, str | list[str] | None]:
        updates: dict[
            str,
            str | list[str] | None,
        ] = {}

        for descriptor, change in patch.ListFields():
            field_name = descriptor.name

            # 매력 포인트는 기존 목록을 통째로 교체
            if field_name == "selling_points":
                updates[field_name] = list(
                    change.values
                )
                continue

            operation = change.WhichOneof(
                "operation"
            )

            # clear는 해당 값을 None으로 초기화
            if operation == "clear":
                updates[field_name] = None
                continue

            if operation != "set_value":
                raise PlanningAgentClientError(
                    reason="MODEL_OUTPUT_INVALID",
                    message=(
                        "모델의 기획서 변경 형식이 "
                        "올바르지 않습니다."
                    ),
                    retryable=False,
                )

            value = change.set_value

            if field_name == "lodging_type":
                try:
                    value = PROTO_TO_LODGING_TYPE[
                        value
                    ].value

                except KeyError as error:
                    raise PlanningAgentClientError(
                        reason="MODEL_OUTPUT_INVALID",
                        message=(
                            "모델이 알 수 없는 숙소 "
                            "유형을 반환했습니다."
                        ),
                        retryable=False,
                    ) from error

            updates[field_name] = value

        return updates

    # 요청과 응답의 식별 정보 및 revision 검사
    def validate_response(
        self,
        request: hotel_ad_v2_pb2.ProcessTurnRequest,
        response: hotel_ad_v2_pb2.ProcessTurnResponse,
    ) -> None:
        if not response.HasField("state_revision"):
            raise PlanningAgentClientError(
                reason="RESPONSE_MISMATCH",
                message=(
                    "모델 응답에 상태 버전이 없습니다."
                ),
                retryable=False,
            )

        matched_fields = {
            "request_id": (
                response.request_id
                == request.request_id
            ),
            "session_id": (
                response.session_id
                == request.session_id
            ),
            "state_revision": (
                response.state_revision
                == request.state_revision
            ),
            "current_step": (
                response.current_step
                == request.current_step
            ),
        }

        mismatched_fields = [
            field_name
            for field_name, matched in matched_fields.items()
            if not matched
        ]

        if mismatched_fields:
            raise PlanningAgentClientError(
                reason="RESPONSE_MISMATCH",
                message=(
                    "모델 응답이 현재 기획 상태와 "
                    "일치하지 않습니다: "
                    + ", ".join(mismatched_fields)
                ),
                retryable=False,
            )

    # protobuf 응답을 React용 응답으로 변환
    def build_domain_response(
        self,
        response: hotel_ad_v2_pb2.ProcessTurnResponse,
    ) -> PlanningTurnResponse:
        try:
            return PlanningTurnResponse(
                request_id=response.request_id,
                session_id=response.session_id,
                message_intent=(
                    PROTO_TO_MESSAGE_INTENT[
                        response.message_intent
                    ]
                ),
                answer_status=(
                    PROTO_TO_ANSWER_STATUS[
                        response.answer_status
                    ]
                ),
                assistant_message=(
                    response.assistant_message
                ),
                brief_updates=(
                    self.parse_brief_updates(
                        response.brief_updates
                    )
                ),
                corrected_fields=[
                    PROTO_TO_BRIEF_FIELD[field]
                    for field in response.corrected_fields
                ],
                completed_fields=[
                    PROTO_TO_BRIEF_FIELD[field]
                    for field in response.completed_fields
                ],
                missing_fields=[
                    PROTO_TO_BRIEF_FIELD[field]
                    for field in response.missing_fields
                ],
                current_step=(
                    PROTO_TO_PLANNING_STEP[
                        response.current_step
                    ]
                ),
                next_step=(
                    PROTO_TO_PLANNING_STEP[
                        response.next_step
                    ]
                ),
                is_complete=response.is_complete,
            )

        except KeyError as error:
            raise PlanningAgentClientError(
                reason="MODEL_OUTPUT_INVALID",
                message=(
                    "모델이 정의되지 않은 상태값을 "
                    "반환했습니다."
                ),
                retryable=False,
            ) from error

        except ValueError as error:
            raise PlanningAgentClientError(
                reason="MODEL_OUTPUT_INVALID",
                message=(
                    "모델 응답 데이터가 올바르지 "
                    "않습니다."
                ),
                retryable=False,
            ) from error

    # 모델 서버에 한 번의 기획 대화 요청
    async def process_turn(
        self,
        session_id: UUID,
        request: PlanningTurnRequest,
        original_image_uploaded: bool,
    ) -> PlanningTurnResponse:
        proto_request = self.build_proto_request(
            session_id=session_id,
            request=request,
            original_image_uploaded=(
                original_image_uploaded
            ),
        )

        try:
            async with grpc.aio.insecure_channel(
                self.grpc_target,
                options=self.channel_options,
            ) as channel:
                stub = (
                    hotel_ad_v2_pb2_grpc
                    .PlanningAgentServiceStub(channel)
                )

                response = await stub.ProcessTurn(
                    proto_request,
                    timeout=self.timeout_seconds,
                )

        except grpc.aio.AioRpcError as error:
            parsed_error = parse_model_rpc_error(
                error=error,
                expected_request_id=(
                    proto_request.request_id
                ),
            )

            raise PlanningAgentClientError(
                reason=parsed_error.reason,
                message=get_safe_model_error_message(
                    "광고 기획",
                    parsed_error,
                ),
                retryable=parsed_error.retryable,
                grpc_code=parsed_error.grpc_code,
                request_id=parsed_error.request_id,
            ) from error

        self.validate_response(
            request=proto_request,
            response=response,
        )

        return self.build_domain_response(
            response
        )

settings = get_settings()

planning_agent_client = GrpcPlanningAgentClient(
    grpc_target=settings.model_grpc_target,
    timeout_seconds=(
        settings.planning_model_timeout_seconds
    ),
    max_message_size_mb=(
        settings.model_grpc_max_message_size_mb
    ),
)