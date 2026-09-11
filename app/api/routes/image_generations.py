from io import BytesIO
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4
import grpc

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings

from app.db.session import get_db
from app.models.image_generation import ImageGeneration
from app.clients.model import ModelServiceError, model_client
from app.schemas.image_generation import (
    ImageGenerationResponse,
    ImageGenerationStatus,
)
from app.services.image_storage import image_storage
from app.services.image_generation_service import (
    image_generation_service,
)

settings = get_settings()

router = APIRouter(
    prefix="/api/image-generations",
    tags=["image-generations"]
)

# 업로드 허용된 이미지 확장자
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp":".webp"
}

# 이미지 최대 크기 설정
max_image_size = settings.max_upload_image_size_mb * 1024 * 1024

@router.post(
    "",
    response_model=ImageGenerationResponse,
    status_code=status.HTTP_201_CREATED
)

# 이미지 생성 요청 POST
async def create_image_generation(
    # 호텔의 이름, 주소 등 광고에 반영할 설명
    hotel_description: Annotated[
        str,
        Form(min_length=1, max_length=2000)
    ],

    # 사용자가 이미지에 넣고 싶은 광고 문구
    ad_copy: Annotated[
        str,
        Form(min_length=1, max_length=500)
    ],

    # 입력 폼에서 이미지 파일
    image: Annotated[
        UploadFile,
        File()
    ],

    # API 요청마다 독립적인 DB 세션 생성
    db: Annotated[
        Session,
        Depends(get_db)
    ],

    # 분위기나 배치 등 선택적인 추가 요청
    additional_instructions: Annotated[
        str | None,
        Form(max_length=2000),
    ] = None,
) -> ImageGeneration:

    # 공백으로만 구성된 필수 입력 방지
    hotel_description = hotel_description.strip()
    ad_copy = ad_copy.strip()

    if not hotel_description:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="호텔 설명을 입력해야 합니다.",
        )

    if not ad_copy:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="광고 문구를 입력해야 합니다.",
        )

    # 선택값은 공백만 입력된 경우 None으로 정리
    if additional_instructions is not None:
        additional_instructions = (
            additional_instructions.strip() or None
        )
        
    # 알맞은 이미지 확장자 확인
    extension = ALLOWED_IMAGE_TYPES.get(image.content_type or "")

    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail = "JPEG, PNG, WebP 이미지만 업로드할 수 있습니다."
        )

    # 업로드 이미지 정보(크기) 확인
    hotel_image_bytes = await image.read()
    file_size = len(hotel_image_bytes)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail = "비어 있는 이미지 파일은 업로드 할 수 없습니다. (크기: 0bytes)"
        )

    # 이미지 크기 최대 설정 (수정: .env)
    if file_size > max_image_size:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=(
                f"이미지 크기는 "
                f"{settings.max_upload_image_size_mb}MB 이하여야 합니다."
            ),
        )

    # DB와 이미지 폴더에서 함꼐 사용할 요청 UUID 생성
    generation_id = uuid4()

    # 브라우저가 전달한 경로를 제거하고 파일명만 보관
    original_filename = Path(
        (image.filename or f"upload{extension}").replace("\\", "/")
    ).name[:255]

    try:
        # 원본 이미지를 저장
        _, original_image_url = image_storage.save_original(
            generation_id = generation_id,
            source = BytesIO(hotel_image_bytes),
            extension = extension
        )

    except (OSError, ValueError) as error:
        # 저장 중 일부 파일이 만들어졌을 경우 정리
        image_storage.delete_original(generation_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "원본 이미지를 저장하지 못했습니다."
        ) from error

    # PostgreSQL에 저장할 이미지 생성 요청 객체
    generation = ImageGeneration(
        id = generation_id,
        hotel_description=hotel_description,
        ad_copy=ad_copy,
        additional_instructions=additional_instructions,
        original_filename = original_filename,
        original_image_url = original_image_url,
        generated_image_url = None,
        status = ImageGenerationStatus.PENDING.value,
        error_message = None
    )

    try:
        db.add(generation)
        db.commit()

    except SQLAlchemyError as error:
        # DB 저장에 실패하면 파일만 남지 않도록 원본 이미지도 삭제 (이미지 <-> DB 일원화)
        db.rollback()
        image_storage.delete_original(generation_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "이미지 생성 요청 정보를 저장하지 못했습니다."
        ) from error

    # DB가 자동 생성한 시각 등의 값을 다시 불러오기
    db.refresh(generation)

    # 모델 호출 시작 전 처리 상태로 변경
    try:
        image_generation_service.mark_processing(
            db=db,
            generation=generation,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    try:
        # 원본 이미지와 광고 정보를 이미지 모델 서버에 전달
        generated_image_bytes, generated_mime_type = (
            await model_client.generate_advertisement_image(
                request_id=str(generation.id),
                hotel_image_bytes=hotel_image_bytes,
                image_mime_type=image.content_type or "",
                hotel_description=hotel_description,
                ad_copy=ad_copy,
                additional_instructions=additional_instructions,
            )
        )

    except ModelServiceError as error:
        # gRPC 상태 코드를 HTTP 상태와 사용자 메시지로 변환
        error_mapping = {
            grpc.StatusCode.INVALID_ARGUMENT: (
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "이미지 모델이 요청 정보를 처리할 수 없습니다.",
            ),
            grpc.StatusCode.RESOURCE_EXHAUSTED: (
                status.HTTP_502_BAD_GATEWAY,
                "모델 서버의 이미지 처리 용량을 초과했습니다.",
            ),
            grpc.StatusCode.UNAVAILABLE: (
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "이미지 모델 서버에 연결할 수 없습니다.",
            ),
            grpc.StatusCode.INTERNAL: (
                status.HTTP_502_BAD_GATEWAY,
                "이미지 모델 서버에서 오류가 발생했습니다.",
            ),
            grpc.StatusCode.DEADLINE_EXCEEDED: (
                status.HTTP_504_GATEWAY_TIMEOUT,
                "이미지 생성 요청 시간이 초과됐습니다.",
            ),
        }

        http_status, error_message = error_mapping.get(
            error.code,
            (
                status.HTTP_502_BAD_GATEWAY,
                "이미지 모델 요청에 실패했습니다.",
            ),
        )

        mark_generation_failed(
            db=db,
            generation=generation,
            error_message=error_message,
        )

        raise HTTPException(
            status_code=http_status,
            detail=error_message,
        ) from error

    except RuntimeError as error:
        # 연결은 성공했지만 빈 이미지 등 잘못된 응답을 받은 경우
        error_message = "이미지 모델이 올바른 결과를 반환하지 않았습니다."

        mark_generation_failed(
            db=db,
            generation=generation,
            error_message=error_message,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error_message,
        ) from error

    # 계약과 다른 이미지 형식이 반환된 경우
    if generated_mime_type.lower() != "image/png":
        error_message = "이미지 모델이 PNG 형식이 아닌 결과를 반환했습니다."

        mark_generation_failed(
            db=db,
            generation=generation,
            error_message=error_message,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error_message,
        )

    try:
        # PNG 파일 저장 후 DB 상태를 completed로 변경
        generation = image_generation_service.complete_generation(
            db=db,
            generation=generation,
            image_bytes=generated_image_bytes,
            extension=".png",
        )

    except (RuntimeError, ValueError) as error:
        error_message = "생성된 결과 이미지를 저장하지 못했습니다."

        mark_generation_failed(
            db=db,
            generation=generation,
            error_message=error_message,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        ) from error

    return generation

# 모델 처리 실패 정보를 DB에 기록
def mark_generation_failed(
    db: Session,
    generation: ImageGeneration,
    error_message: str,
) -> None:
    try:
        image_generation_service.mark_failed(
            db=db,
            generation=generation,
            error_message=error_message,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이미지 생성 실패 상태를 저장하지 못했습니다.",
        ) from error

# 요청 UUID를 이용해 이미지 생성 기록 조회
@router.get(
    "/{generation_id}",
    response_model=ImageGenerationResponse
)
def read_image_generation(
    generation_id: UUID,
    db: Annotated[
        Session,
        Depends(get_db)
    ],
) -> ImageGeneration:
    # 기본 UUID로 이미지 생성 기록 조회
    generation = db.get(
        ImageGeneration,
        generation_id
    )

    # 해당되는 UUID가 없다면 404
    if generation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "이미지 생성 요청 기록을 찾을 수 없습니다."
        )

    return generation