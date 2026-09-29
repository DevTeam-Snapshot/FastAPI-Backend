# V2 광고 초안 이미지 gRPC 클라이언트
from google.protobuf import empty_pb2
import grpc

from app.clients.draft_image import (
    DraftGenerationRequest,
    DraftImageClient,
    DraftImageClientError,
    DraftImageResult,
)
from app.grpc_stubs import (
    hotel_ad_v2_pb2,
    hotel_ad_v2_pb2_grpc,
)
from app.models.enums import DraftDirection
from app.core.config import get_settings

from app.clients.grpc_error import (
    get_safe_model_error_message,
    parse_model_rpc_error,
)


# 백엔드 숙소 유형을 protobuf Enum으로 변환
LODGING_TYPE_TO_PROTO = {
    "hotel": hotel_ad_v2_pb2.LODGING_TYPE_HOTEL,
    "motel": hotel_ad_v2_pb2.LODGING_TYPE_MOTEL,
    "resort": hotel_ad_v2_pb2.LODGING_TYPE_RESORT,
    "pension": hotel_ad_v2_pb2.LODGING_TYPE_PENSION,
    "other": hotel_ad_v2_pb2.LODGING_TYPE_OTHER,
}


# 백엔드 초안 방향을 protobuf Enum으로 변환
DIRECTION_TO_PROTO = {
    DraftDirection.ROOM: hotel_ad_v2_pb2.DRAFT_DIRECTION_ROOM,
    DraftDirection.EMOTION: hotel_ad_v2_pb2.DRAFT_DIRECTION_EMOTION,
    DraftDirection.BENEFIT: hotel_ad_v2_pb2.DRAFT_DIRECTION_BENEFIT,
}


class GrpcDraftImageClient:
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
    # 광고 초안 이미지 서비스 준비 상태 확인
    async def health_check(self) -> bool:
        try:
            async with grpc.aio.insecure_channel(
                self.grpc_target,
                options=self.channel_options,
            ) as channel:
                stub = (
                    hotel_ad_v2_pb2_grpc
                    .DraftImageServiceStub(channel)
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

            raise DraftImageClientError(
                reason=parsed_error.reason,
                message=get_safe_model_error_message(
                    "광고 초안 생성",
                    parsed_error,
                ),
                retryable=parsed_error.retryable,
                grpc_code=parsed_error.grpc_code,
                request_id=parsed_error.request_id,
            ) from error

        return response.healthy

    # 백엔드 요청 객체를 protobuf 요청 메시지로 변환
    def build_proto_request(
        self,
        request: DraftGenerationRequest,
    ) -> hotel_ad_v2_pb2.GenerateDraftRequest:
        try:
            lodging_type = LODGING_TYPE_TO_PROTO[
                request.brief.lodging_type
            ]

        except KeyError as error:
            raise ValueError(
                "지원하지 않는 숙소 유형입니다."
            ) from error

        brief = hotel_ad_v2_pb2.AdvertisementBrief(
            lodging_type=lodging_type,
            lodging_name=request.brief.lodging_name,
            location=request.brief.location,
            selling_points=list(
                request.brief.selling_points
            ),
            lodging_service=list(
                request.brief.lodging_service
            ),
            mood=request.brief.mood,
            color_preference=(
                request.brief.color_preference
            ),
            target_audience=request.brief.target_audience,
            ad_copy=request.brief.ad_copy,
        )

        # OTHER 유형일 때만 상세 숙소 유형 전달
        if request.brief.lodging_type_detail is not None:
            brief.lodging_type_detail = (
                request.brief.lodging_type_detail
            )

        return hotel_ad_v2_pb2.GenerateDraftRequest(
            request_id=request.request_id,
            session_id=str(request.session_id),
            draft_id=str(request.draft_id),
            generation_round=request.generation_round,
            is_regeneration=request.is_regeneration,
            direction=DIRECTION_TO_PROTO[
                request.direction
            ],
            brief=brief,
            original_image_bytes=(
                request.original_image_bytes
            ),
            image_mime_type=request.image_mime_type,
        )

    # 요청과 응답의 식별값이 일치하는지 검사
    def validate_response(
        self,
        request: hotel_ad_v2_pb2.GenerateDraftRequest,
        response: hotel_ad_v2_pb2.GenerateDraftResponse,
    ) -> None:
        matched_fields = {
            "request_id": (
                response.request_id
                == request.request_id
            ),
            "session_id": (
                response.session_id
                == request.session_id
            ),
            "draft_id": (
                response.draft_id
                == request.draft_id
            ),
            "generation_round": (
                response.generation_round
                == request.generation_round
            ),
            "direction": (
                response.direction
                == request.direction
            ),
        }

        mismatched_fields = [
            field_name
            for field_name, matched in matched_fields.items()
            if not matched
        ]

        if mismatched_fields:
            raise DraftImageClientError(
                reason="RESPONSE_MISMATCH",
                message=(
                    "모델 응답의 식별 정보가 요청과 "
                    "일치하지 않습니다: "
                    + ", ".join(mismatched_fields)
                ),
                retryable=False,
            )

    # 모델 서버에 광고 초안 한 장 생성 요청
    async def generate_draft(
        self,
        request: DraftGenerationRequest,
    ) -> DraftImageResult:
        proto_request = self.build_proto_request(
            request
        )

        try:
            async with grpc.aio.insecure_channel(
                self.grpc_target,
                options=self.channel_options,
            ) as channel:
                stub = (
                    hotel_ad_v2_pb2_grpc
                    .DraftImageServiceStub(channel)
                )

                response = await stub.GenerateDraft(
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

            raise DraftImageClientError(
                reason=parsed_error.reason,
                message=get_safe_model_error_message(
                    "광고 초안 생성",
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

        return DraftImageResult(
            image_bytes=response.image_bytes,
            image_mime_type=response.image_mime_type,
        )

settings = get_settings()

draft_image_client: DraftImageClient = (
    GrpcDraftImageClient(
        grpc_target=settings.model_grpc_target,
        timeout_seconds=(
            settings.draft_model_timeout_seconds
        ),
        max_message_size_mb=(
            settings.model_grpc_max_message_size_mb
        ),
    )
)