import grpc

from app.core.config import get_settings
from app.grpc_stubs import (
    hotel_advertisement_image_pb2,
    hotel_advertisement_image_pb2_grpc,
)


# 모델 서버가 gRPC 오류를 반환했을 때 사용하는 예외
class ModelServiceError(ConnectionError):
    def __init__(
        self,
        code: grpc.StatusCode,
        details: str,
    ) -> None:
        self.code = code
        self.details = details

        super().__init__(
            f"이미지 모델 서버 요청 실패: {code.name}"
        )


# 이미지 모델 서버와 통신하는 클라이언트
class ModelClient:
    def __init__(self) -> None:
        settings = get_settings()

        self.grpc_target = settings.model_grpc_target
        self.timeout = settings.model_timeout_seconds

        # MiB 설정값을 byte 단위로 변환
        max_message_size = (
            settings.model_grpc_max_message_size_mb
            * 1024
            * 1024
        )

        # 원본 이미지와 결과 이미지를 주고받기 위한 gRPC 용량 설정
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

    # 이미지 모델 서버의 실행 상태 확인
    async def health_check(self) -> bool:
        try:
            async with grpc.aio.insecure_channel(
                self.grpc_target,
                options=self.channel_options,
            ) as channel:
                stub = (
                    hotel_advertisement_image_pb2_grpc
                    .HotelAdvertisementImageServiceStub(channel)
                )

                response = await stub.HealthCheck(
                    hotel_advertisement_image_pb2.HealthCheckRequest(),
                    timeout=self.timeout,
                )

                return response.healthy

        except grpc.aio.AioRpcError as error:
            raise ModelServiceError(
                code=error.code(),
                details=error.details() or "",
            ) from error

    # 원본 이미지와 광고 정보를 모델 서버에 전달
    async def generate_advertisement_image(
        self,
        request_id: str,
        hotel_image_bytes: bytes,
        image_mime_type: str,
        hotel_description: str,
        ad_copy: str,
        additional_instructions: str | None = None,
    ) -> tuple[bytes, str]:
        request = (
            hotel_advertisement_image_pb2
            .GenerateAdvertisementImageRequest(
                request_id=request_id,
                hotel_image_bytes=hotel_image_bytes,
                image_mime_type=image_mime_type,
                hotel_description=hotel_description,
                ad_copy=ad_copy,
                additional_instructions=(
                    additional_instructions or ""
                ),
            )
        )

        try:
            async with grpc.aio.insecure_channel(
                self.grpc_target,
                options=self.channel_options,
            ) as channel:
                stub = (
                    hotel_advertisement_image_pb2_grpc
                    .HotelAdvertisementImageServiceStub(channel)
                )

                response = await stub.GenerateAdvertisementImage(
                    request,
                    timeout=self.timeout,
                )

        except grpc.aio.AioRpcError as error:
            raise ModelServiceError(
                code=error.code(),
                details=error.details() or "",
            ) from error

        # 정상 응답인데 이미지가 비어 있는 경우 방어
        if not response.image_bytes:
            raise RuntimeError(
                "이미지 모델 서버가 빈 결과를 반환했습니다."
            )

        return (
            bytes(response.image_bytes),
            response.image_mime_type,
        )


# 여러 API에서 재사용할 모델 클라이언트 객체
model_client = ModelClient()