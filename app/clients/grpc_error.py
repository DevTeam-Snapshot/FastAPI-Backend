# V2 모델 서버의 구조화 gRPC 오류 해석

from dataclasses import dataclass

import grpc
from grpc_status import rpc_status

from app.grpc_stubs import hotel_ad_v2_pb2


@dataclass(frozen=True)
class ParsedModelRpcError:
    grpc_code: grpc.StatusCode
    request_id: str | None
    reason: str
    retryable: bool


# 구조화 상세 정보가 없을 때 사용할 기본 오류 코드
DEFAULT_REASON_BY_GRPC_CODE = {
    grpc.StatusCode.INVALID_ARGUMENT: (
        "INVALID_ARGUMENT"
    ),
    grpc.StatusCode.FAILED_PRECONDITION: (
        "FAILED_PRECONDITION"
    ),
    grpc.StatusCode.RESOURCE_EXHAUSTED: (
        "RESOURCE_EXHAUSTED"
    ),
    grpc.StatusCode.UNAVAILABLE: (
        "TRANSPORT_UNAVAILABLE"
    ),
    grpc.StatusCode.DEADLINE_EXCEEDED: (
        "RESULT_UNKNOWN"
    ),
    grpc.StatusCode.INTERNAL: (
        "INTERNAL_ERROR"
    ),
    grpc.StatusCode.CANCELLED: (
        "REQUEST_CANCELLED"
    ),
}

# 모델 서버와 합의된 reason별 gRPC 코드와 재시도 가능 여부
MODEL_ERROR_RULES = {
    "INVALID_EVENT": (
        grpc.StatusCode.INVALID_ARGUMENT,
        False,
    ),
    "INVALID_GENERATION_ROUND": (
        grpc.StatusCode.INVALID_ARGUMENT,
        False,
    ),
    "CONTEXT_TOO_LARGE": (
        grpc.StatusCode.INVALID_ARGUMENT,
        False,
    ),
    "INVALID_ARGUMENT": (
        grpc.StatusCode.INVALID_ARGUMENT,
        False,
    ),
    "INVALID_IMAGE": (
        grpc.StatusCode.INVALID_ARGUMENT,
        False,
    ),
    "BRIEF_READ_ONLY": (
        grpc.StatusCode.FAILED_PRECONDITION,
        False,
    ),
    "BRIEF_INCOMPLETE": (
        grpc.StatusCode.FAILED_PRECONDITION,
        False,
    ),
    "GENERATION_REJECTED": (
        grpc.StatusCode.FAILED_PRECONDITION,
        False,
    ),
    "INPUT_TOO_LARGE": (
        grpc.StatusCode.RESOURCE_EXHAUSTED,
        False,
    ),
    "UPSTREAM_RATE_LIMIT": (
        grpc.StatusCode.RESOURCE_EXHAUSTED,
        True,
    ),
    "SERVER_BUSY": (
        grpc.StatusCode.RESOURCE_EXHAUSTED,
        True,
    ),
    "UPSTREAM_UNAVAILABLE": (
        grpc.StatusCode.UNAVAILABLE,
        True,
    ),
    "RESULT_UNKNOWN": (
        grpc.StatusCode.DEADLINE_EXCEEDED,
        False,
    ),
    "MODEL_OUTPUT_INVALID": (
        grpc.StatusCode.INTERNAL,
        False,
    ),
    "COMPOSITION_FAILED": (
        grpc.StatusCode.INTERNAL,
        False,
    ),
    "OUTPUT_TOO_LARGE": (
        grpc.StatusCode.INTERNAL,
        False,
    ),
    "INTERNAL_ERROR": (
        grpc.StatusCode.INTERNAL,
        False,
    ),
    "REQUEST_CANCELLED": (
        grpc.StatusCode.CANCELLED,
        False,
    ),
}

def parse_model_rpc_error(
    error: grpc.aio.AioRpcError,
    expected_request_id: str | None = None,
) -> ParsedModelRpcError:
    grpc_code = error.code()

    default_error = ParsedModelRpcError(
        grpc_code=grpc_code,
        request_id=None,
        reason=DEFAULT_REASON_BY_GRPC_CODE.get(
            grpc_code,
            "TRANSPORT_ERROR",
        ),
        # 구조화 정보가 없으면 자동 재시도하지 않음
        retryable=False,
    )

    try:
        status_message = rpc_status.from_call(
            error
        )

    except (ValueError, TypeError):
        return default_error

    if status_message is None:
        return default_error

    for packed_detail in status_message.details:
        detail = hotel_ad_v2_pb2.ModelErrorDetail()

        if not packed_detail.Unpack(detail):
            continue

 # 다른 요청의 오류 상세 정보가 섞인 경우 차단
        if (
            expected_request_id is not None
            and detail.request_id
            != expected_request_id
        ):
            return ParsedModelRpcError(
                grpc_code=grpc_code,
                request_id=detail.request_id or None,
                reason="RESPONSE_MISMATCH",
                retryable=False,
            )

        rule = MODEL_ERROR_RULES.get(
            detail.reason
        )

        # 알 수 없는 reason 또는 계약과 다른 조합 차단
        if (
            rule is None
            or rule[0] != grpc_code
            or rule[1] != detail.retryable
        ):
            return ParsedModelRpcError(
                grpc_code=grpc_code,
                request_id=detail.request_id or None,
                reason="MALFORMED_ERROR_DETAIL",
                retryable=False,
            )

        return ParsedModelRpcError(
            grpc_code=grpc_code,
            request_id=detail.request_id or None,
            reason=detail.reason,
            retryable=detail.retryable,
        )

    return default_error


# provider 원문을 노출하지 않는 사용자용 안전한 오류 메시지
def get_safe_model_error_message(
    service_name: str,
    error: ParsedModelRpcError,
) -> str:
    messages = {
        grpc.StatusCode.INVALID_ARGUMENT: (
            "요청 데이터가 올바르지 않습니다."
        ),
        grpc.StatusCode.FAILED_PRECONDITION: (
            "현재 상태에서는 요청을 처리할 수 없습니다."
        ),
        grpc.StatusCode.RESOURCE_EXHAUSTED: (
            "모델 서버의 처리 한도를 초과했습니다."
        ),
        grpc.StatusCode.UNAVAILABLE: (
            "모델 서버에 연결할 수 없습니다."
        ),
        grpc.StatusCode.DEADLINE_EXCEEDED: (
            "모델 서버의 응답 시간이 초과됐습니다."
        ),
        grpc.StatusCode.INTERNAL: (
            "모델 서버 내부에서 오류가 발생했습니다."
        ),
        grpc.StatusCode.CANCELLED: (
            "모델 요청이 취소됐습니다."
        ),
    }

    message = messages.get(
        error.grpc_code,
        "모델 요청을 처리하지 못했습니다.",
    )

    return f"{service_name}: {message}"