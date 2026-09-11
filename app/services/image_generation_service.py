import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.image_generation import ImageGeneration
from app.schemas.image_generation import ImageGenerationStatus
from app.services.image_storage import ImageStorage, image_storage
from app.core.config import get_settings

# 파일에 대한 서버 로그 기록
logger  = logging.getLogger(__name__)

# 생성 이미지 저장, DB에 상태 변경 처리
class ImageGenerationService:
    def __init__(
            self,
            storage: ImageStorage,
            keep_original_images: bool
    ) -> None:
        self.storage = storage
        self.keep_original_images = keep_original_images

    # 모델 처리를 위해 Processing으로 변경
    def mark_processing(
            self,
            db: Session,
            generation: ImageGeneration
    ) -> ImageGeneration:
        generation.status = ImageGenerationStatus.PROCESSING.value
        # 에러가 난다면 보통 DB 관련 문제(접근 권한, 용량 부족, 연결 문제 등)
        generation.error_message = None

        try:
            db.commit()

        except SQLAlchemyError as error:
            db.rollback()

            raise RuntimeError(
                "이미지 생성 처리 상태를 업데이트 하지 못했습니다."
            ) from error

        db.refresh(generation)

        return generation

    # 모델 호출이나 이미지 생성이 실패한 경우 FAILED로 변경
    def mark_failed(
            self,
            db: Session,
            generation: ImageGeneration,
            error_message: str
    ) -> ImageGeneration:
        generation.status = ImageGenerationStatus.FAILED.value
        generation.generated_image_url = None
        generation.error_message = error_message

        try:
            db.commit()

        except SQLAlchemyError as error:
            db.rollback()

            # FAILED를 DB에 반영 하지 못함
            raise RuntimeError(
                "이미지 생성 실패에 대한 정보를 저장하지 못했습니다."
            ) from error
        
        db.refresh(generation)

        return generation

    # 생성된 이미지 데이터를 저장하고 PENDING -> COMPLETED로 변경
    def complete_generation(
            self,
            db: Session,
            generation: ImageGeneration,
            image_bytes: bytes,
            extension: str = ".png"
    ) -> ImageGeneration:
        
        # 이미지가 없다면 저장 하지않음
        if not image_bytes:
            raise ValueError("생성된 이미지 데이터가 없습니다.")

        try:
            # 생성 결과 이미지를 Image/results 폴더에 저장
            _, generated_image_url = self.storage.save_generated(
                generation_id = generation.id,
                image_bytes = image_bytes,
                extension = extension
            )

        except (OSError, ValueError) as error:
            try:
                self.storage.delete_generated(generation.id)

            except OSError:
                logger.exception(
                    "결과 이미지 저장 실패 후 파일 정리에도 실패했습니다."
                )
                
            raise RuntimeError(
                "생성된 결과 이미지를 저장하지 못했습니다."
            ) from error

        # 생성 결과 이미지 URL과 처리 상태를 DB에 반영
        generation.generated_image_url = generated_image_url
        generation.status = ImageGenerationStatus.COMPLETED.value
        generation.error_message = None

        # 원본 저장 X 설정이라면 (.env)
        if not self.keep_original_images:
            # 원본 URL 제거
            generation.original_image_url = None

        try:
            db.commit()

        except SQLAlchemyError as error:
            db.rollback()

            # DB 저장 실패시
            try:
                self.storage.delete_generated(generation.id)

            except OSError:
                logger.exception(
                    "DB 저장 실패 후 결과 이미지 정리에도 실패했습니다."
                )
            raise RuntimeError(
                "이미지 생성 완료 정보를 DB에 저장하지 못했습니다."
            ) from error

        # DB 저장 성공 시
        # 만약 원본 저장 X 설정이라면
        if not self.keep_original_images:
            try:
                # 원본 URL 삭제
                self.storage.delete_original(generation.id)

            # 원본 URL 삭제 실패 시
            except OSError:
                logger.exception(
                    "생성 완료 후 원본 이미지를 삭제하지 못했습니다."
                )

        # DB 새로고침
        db.refresh(generation)

        return generation

# 서비스 객체 생성
settings = get_settings()

image_generation_service = ImageGenerationService(
    storage = image_storage,
    keep_original_images=settings.keep_original_images
)