# V2 광고 초안 이미지 생성 처리 서비스

import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.clients.draft_image import (
    AdvertisementBriefData,
    DraftGenerationRequest,
    DraftImageClient,
    DraftImageClientError,
    DraftImageResult
)

from app.clients.grpc_draft_image import (
    draft_image_client,
)

from app.services.advertisement_draft_service import (
    advertisement_draft_service,
)

from app.models.advertisement_draft import AdvertisementDraft
from app.models.enums import (
    AdvertisementDraftStatus,
    DraftDirection,
)
from app.models.planning_session import PlanningSession
from app.services.image_storage import (
    ImageStorage,
    image_storage,
)
from app.services.image_validation import (
    ImageValidationError,
    ImageValidator,
    NormalizedImage,
    image_validator,
)

from app.core.config import get_settings


logger = logging.getLogger(__name__)

# 모델 결과 검증 또는 파일 저장 실패
class DraftResultProcessingError(RuntimeError):
    def __init__(
        self,
        error_code: str,
        message: str,
    ) -> None:
        self.error_code = error_code
        self.message = message

        super().__init__(message)

class DraftGenerationService:
    def __init__(
            self,
            client: DraftImageClient,
            storage: ImageStorage,
            validator: ImageValidator,
            expected_width: int,
            expected_height: int,
    ) -> None:
        self.client = client
        self.storage = storage
        self.validator = validator
        self.expected_width = expected_width
        self.expected_height = expected_height

    # DB의 확정 기획서를 모델 요청 형식으로 변환
    def build_brief(
        self,
        planning_session: PlanningSession,
    ) -> AdvertisementBriefData:
        required_fields = {
            "lodging_type": planning_session.lodging_type,
            "lodging_name": planning_session.lodging_name,
            "location": planning_session.location,
            "selling_points": planning_session.selling_points,
            "lodging_service": planning_session.lodging_service,
            "mood": planning_session.mood,
            "color_preference": planning_session.color_preference,
            "target_audience": planning_session.target_audience,
            "ad_copy": planning_session.ad_copy,
        }

        missing_fields = [
            field_name
            for field_name, value in required_fields.items()
            if not value
        ]

        if missing_fields:
            raise ValueError(
                "확정 기획서의 필수 정보가 누락되었습니다: "
                + ", ".join(missing_fields)
            )

        if (
            planning_session.lodging_type == "other"
            and not planning_session.lodging_type_detail
        ):
            raise ValueError(
                "기타 숙소 유형의 상세 정보가 없습니다."
            )

        return AdvertisementBriefData(
            lodging_type=planning_session.lodging_type,
            lodging_type_detail=(
                planning_session.lodging_type_detail
            ),
            lodging_name=planning_session.lodging_name,
            location=planning_session.location,
            selling_points=tuple(
                planning_session.selling_points
            ),
            lodging_service=tuple(
                planning_session.lodging_service
            ),
            mood=planning_session.mood,
            color_preference=(
                planning_session.color_preference
            ),
            target_audience=(
                planning_session.target_audience
            ),
            ad_copy=planning_session.ad_copy,
        )

    # 저장된 원본 이미지를 읽고 모델 입력용 JPEG로 정규화
    def load_normalized_image(
        self,
        planning_session: PlanningSession,
    ) -> NormalizedImage:
        if planning_session.original_image_url is None:
            raise ValueError(
                "기획 세션에 원본 이미지가 없습니다."
            )

        if planning_session.original_mime_type is None:
            raise ValueError(
                "원본 이미지의 MIME 타입이 없습니다."
            )

        try:
            original_image_bytes = self.storage.read_original(
                planning_session.id
            )

        except OSError as error:
            raise RuntimeError(
                "저장된 원본 이미지를 읽지 못했습니다."
            ) from error

        return self.validator.normalize_for_model(
            image_bytes=original_image_bytes,
            declared_mime_type=(
                planning_session.original_mime_type
            ),
        )

    # 세션·초안 정보를 하나의 모델 요청 객체로 구성
    def build_request(
        self,
        planning_session: PlanningSession,
        draft: AdvertisementDraft,
        brief: AdvertisementBriefData,
        normalized_image: NormalizedImage,
    ) -> DraftGenerationRequest:
        try:
            direction = DraftDirection(draft.direction)

        except ValueError as error:
            raise ValueError(
                "지원하지 않는 광고 초안 방향입니다."
            ) from error

        return DraftGenerationRequest(
            request_id=str(uuid4()),
            session_id=planning_session.id,
            draft_id=draft.id,
            generation_round=draft.generation_round,
            is_regeneration=(
                draft.generation_round == 2
            ),
            direction=direction,
            brief=brief,
            original_image_bytes=(
                normalized_image.image_bytes
            ),
            image_mime_type=normalized_image.mime_type,
        )

    # 모델 호출 전에 초안들을 processing 상태로 변경
    def mark_processing(
        self,
        db: Session,
        drafts: list[AdvertisementDraft],
    ) -> None:
        for draft in drafts:
            draft.status = (
                AdvertisementDraftStatus.PROCESSING.value
            )
            draft.error_code = None
            draft.error_message = None

        try:
            db.commit()

        except SQLAlchemyError as error:
            db.rollback()

            raise RuntimeError(
                "광고 초안 처리 상태를 저장하지 못했습니다."
            ) from error

        for draft in drafts:
            db.refresh(draft)


    # 모델 호출 또는 결과 처리에 실패한 초안 저장
    def mark_failed(
        self,
        db: Session,
        draft: AdvertisementDraft,
        error_code: str,
        error_message: str,
    ) -> AdvertisementDraft:
        draft.status = AdvertisementDraftStatus.FAILED.value
        draft.image_url = None
        draft.file_size = None
        draft.error_code = error_code
        draft.error_message = error_message
        draft.completed_at = None

        try:
            db.commit()

        except SQLAlchemyError as error:
            db.rollback()

            raise RuntimeError(
                "광고 초안 실패 정보를 저장하지 못했습니다."
            ) from error

        db.refresh(draft)

        return draft

    # 모델 결과 PNG를 저장하고 completed 상태로 변경
    def complete_draft(
        self,
        db: Session,
        draft: AdvertisementDraft,
        result: DraftImageResult,
    ) -> AdvertisementDraft:
        if result.image_mime_type != "image/png":
            raise DraftResultProcessingError(
                error_code="MODEL_OUTPUT_INVALID",
                message="모델 결과의 MIME 타입이 image/png가 아닙니다.",
            )

        try:
            validated_image = self.validator.validate_upload(
                image_bytes=result.image_bytes,
                declared_mime_type=result.image_mime_type,
            )

        except ImageValidationError as error:
            raise DraftResultProcessingError(
                error_code="MODEL_OUTPUT_INVALID",
                message="모델이 올바르지 않은 PNG 이미지를 반환했습니다.",
            ) from error

        # V2 모델 결과는 4:5 비율로
        if (
            validated_image.width != self.expected_width
            or validated_image.height != self.expected_height
        ):
            raise DraftResultProcessingError(
                error_code="MODEL_OUTPUT_INVALID",
                message=(
                    "모델 결과 이미지의 크기가 "
                    f"{self.expected_width}x"
                    f"{self.expected_height}가 아닙니다."
                ),
            )

        try:
            _, image_url = self.storage.save_generated(
                generation_id=draft.id,
                image_bytes=result.image_bytes,
                extension=".png",
            )

        except (OSError, ValueError) as error:
            try:
                self.storage.delete_generated(draft.id)

            except OSError:
                logger.exception(
                    "초안 이미지 저장 실패 후 파일 정리에도 실패했습니다."
                )

            raise DraftResultProcessingError(
                error_code="RESULT_STORAGE_FAILED",
                message="생성된 광고 초안 이미지를 저장하지 못했습니다.",
            ) from error

        draft.status = AdvertisementDraftStatus.COMPLETED.value
        draft.image_url = image_url
        draft.mime_type = validated_image.mime_type
        draft.file_size = validated_image.file_size
        draft.error_code = None
        draft.error_message = None
        draft.completed_at = datetime.now(timezone.utc)

        try:
            db.commit()

        except SQLAlchemyError as error:
            db.rollback()

            try:
                self.storage.delete_generated(draft.id)

            except OSError:
                logger.exception(
                    "초안 DB 저장 실패 후 결과 파일 정리에도 실패했습니다."
                )

            raise RuntimeError(
                "광고 초안 완료 정보를 저장하지 못했습니다."
            ) from error

        db.refresh(draft)

        return draft

    # A·B·C 초안을 모델에 동시에 요청하고 결과를 각각 저장
    async def generate_drafts(
        self,
        db: Session,
        planning_session: PlanningSession,
        drafts: list[AdvertisementDraft],
    ) -> list[AdvertisementDraft]:
        if not drafts:
            raise ValueError(
                "생성할 광고 초안이 없습니다."
            )

        # pending 상태인 초안만 실제 모델에 요청
        target_drafts = [
            draft
            for draft in drafts
            if draft.status == AdvertisementDraftStatus.PENDING.value
        ]

        if not target_drafts:
            raise ValueError(
                "생성 대기 상태인 광고 초안이 없습니다."
            )

        # 모델 호출 전에 공통 입력을 한 번만 구성
        brief = self.build_brief(planning_session)
        normalized_image = self.load_normalized_image(
            planning_session
        )

        requests = [
            self.build_request(
                planning_session=planning_session,
                draft=draft,
                brief=brief,
                normalized_image=normalized_image,
            )
            for draft in target_drafts
        ]

        # 세 초안을 한 번에 processing 상태로 변경
        self.mark_processing(
            db=db,
            drafts=target_drafts,
        )

        # DB 세션을 건드리지 않는 모델 호출만 동시에 실행
        results = await asyncio.gather(
            *(
                self.client.generate_draft(request)
                for request in requests
            ),
            return_exceptions=True,
        )

        # 모델 결과는 하나씩 순서대로 파일과 DB에 반영
        for draft, result in zip(
            target_drafts,
            results,
            strict=True,
        ):
            if isinstance(
                result,
                DraftImageClientError,
            ):
                self.mark_failed(
                    db=db,
                    draft=draft,
                    error_code=result.reason,
                    error_message=result.message,
                )
                continue

            if isinstance(result, Exception):
                logger.error(
                    "예상하지 못한 초안 모델 호출 오류",
                    exc_info=(
                        type(result),
                        result,
                        result.__traceback__,
                    ),
                )

                self.mark_failed(
                    db=db,
                    draft=draft,
                    error_code="MODEL_REQUEST_FAILED",
                    error_message=(
                        "광고 초안 모델 요청에 실패했습니다."
                    ),
                )
                continue

            try:
                self.complete_draft(
                    db=db,
                    draft=draft,
                    result=result,
                )

            except DraftResultProcessingError as error:
                self.mark_failed(
                    db=db,
                    draft=draft,
                    error_code=error.error_code,
                    error_message=error.message,
                )

            except RuntimeError:
                logger.exception(
                    "광고 초안 완료 정보 저장 중 오류가 발생했습니다."
                )

                self.mark_failed(
                    db=db,
                    draft=draft,
                    error_code="RESULT_PERSISTENCE_FAILED",
                    error_message=(
                        "광고 초안 결과를 저장하지 못했습니다."
                    ),
                )

        # 2회차 세 장이 모두 성공했을 때만 재생성 기회 사용 처리
        if (
            drafts[0].generation_round == 2
            and all(
                draft.status
                == AdvertisementDraftStatus.COMPLETED.value
                for draft in drafts
            )
        ):
            advertisement_draft_service.mark_regeneration_succeeded(
                db=db,
                planning_session=planning_session,
            )

        return drafts

settings = get_settings()

draft_generation_service = DraftGenerationService(
    client=draft_image_client,
    storage=image_storage,
    validator=image_validator,
    expected_width=settings.draft_image_width,
    expected_height=settings.draft_image_height,
)