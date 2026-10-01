# V2 광고 초안 이미지 모델 클라이언트

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID
import grpc

from app.models.enums import DraftDirection

# 모델에 전달할 확정 광고 기획서
@dataclass(frozen=True)
class AdvertisementBriefData:
    lodging_type: str
    lodging_type_detail: str | None
    lodging_name: str
    location: str
    selling_points: tuple[str, ...]
    lodging_service: tuple[str, ...]
    mood: str
    color_preference: str
    target_audience: str
    ad_copy: str


# 초안 이미지 생성 요청
@dataclass(frozen=True)
class DraftGenerationRequest:
    request_id: str
    session_id: UUID
    draft_id: UUID
    generation_round: int
    is_regeneration: bool
    direction: DraftDirection
    brief: AdvertisementBriefData
    original_image_bytes: bytes
    image_mime_type: str

    def __post_init__(self) -> None:
        # 최초 생성, 재생성
        if self.generation_round not in {1, 2}:
            raise ValueError(
                "generation_round는 1 또는 2 여야 합니다."
            )
        
        # 1회차는 False, 2회차는 True여야 함
        if self.is_regeneration != (
            self.generation_round == 2
        ):
            raise ValueError(
                "생성 회차와 재생성 여부가 일치하지 않습니다."
            )

        if not self.original_image_bytes:
            raise ValueError(
                "모델에 전달할 원본 이미지가 없습니다."
            )

# 모델이 반환하는 이미지 결과
@dataclass(frozen = True)
class DraftImageResult:
    image_bytes: bytes
    image_mime_type: str

class DraftImageClientError(RuntimeError):
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


# gRPC 클라이언트가 지킬 공통 형식
class DraftImageClient(Protocol):
    async def generate_draft(
        self,
        request: DraftGenerationRequest,
    ) -> DraftImageResult:
        ...