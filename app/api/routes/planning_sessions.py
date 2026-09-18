from typing import Annotated
from uuid import UUID
from io import BytesIO
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.planning_session import PlanningSession
from app.schemas.planning_session import PlanningSessionConfirmRequest, PlanningSessionResponse
from app.services.planning_session_service import planning_session_service
from app.models.enums import PlanningSessionStatus
from app.services.image_storage import image_storage
from app.services.image_validation import (
    ImageValidationError,
    image_validator,
)

# 광고 기획 세션 API의 공통 URL 태그
router = APIRouter(
    prefix = "/api/planning-sessions",
    tags = ["planning-sessions"]
    )

# 새로운 광고 기획 세션 생성
@router.post(
    "",
    response_model=PlanningSessionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_planning_session(
    db: Annotated[
        Session,
        Depends(get_db)
    ]
) -> PlanningSession:
    try:
        return planning_session_service.create_session(db)

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = str(error)
        ) from error                                            # 광고 기획 세션을 생성하지 못했습니다.

# UUID에 해당되는 광고 기획 세션 조회
@router.get(
    "/{session_id}",
    response_model=PlanningSessionResponse
)
def read_planning_session(
    session_id: UUID,
    db: Annotated[
        Session,
        Depends(get_db)
    ]
) -> PlanningSession:
    try:
        planning_session = planning_session_service.get_session(
            db = db,
            session_id=session_id
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = str(error)
        ) from error                                                # 해당 광고 기획 세션을 조회하지 못했습니다.

    if planning_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "광고 기획 세션을 찾을 수 없습니다."
        )

    return planning_session

# 기획 세션에 원본 이미지 업로드
@router.post(
    "/{session_id}/original-image",
    response_model=PlanningSessionResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_original_image(
    session_id: UUID,
    image: Annotated[
        UploadFile,
        File()
    ],

    db: Annotated[
        Session,
        Depends(get_db)
    ]
)-> PlanningSession:
    # 이미지를 저장할 기획 세션 조회
    try: 
        planning_session = planning_session_service.get_session(
            db = db,
            session_id = session_id
        )
    except RuntimeError as error:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = str(error)                                     # 해당 세션을 조회하지 못했습니다.
        ) from error

    if planning_session is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "광고 기획 세션을 찾을 수 없습니다."
        )

    if planning_session.status != PlanningSessionStatus.PLANNING.value:
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = "기획이 완료된 세션에는 이미지를 업로드할 수 없습니다."
        )

    # 세션당 원본 이미지 한장만 저장
    if planning_session.original_image_url is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail = "원본 이미지가 이미 등록된 세션입니다."
        )

    declared_mime_type = image.content_type or ""

    # 지원하지 않는 이미지 확장자 차단
    allowed_mime_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if declared_mime_type not in allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="JPEG, PNG, WebP 이미지만 업로드할 수 있습니다.",
        )

    # 브라우저가 전달한 경로를 제거하고 파일명만 보관
    original_filename = Path(
        image.filename or "upload"
    ).name[:255]

    try:
        image_bytes = await image.read()

    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="업로드한 이미지 파일을 읽지 못했습니다.",
        ) from error

    finally:
        await image.close()

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비어 있는 이미지 파일은 업로드할 수 없습니다.",
        )

    if len(image_bytes) > image_validator.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=(
                f"이미지 크기는 "
                f"{image_validator.max_file_size_mb}MB 이하여야 합니다."
            ),
        )

    try:
        # MIME 타입, 실제 이미지 형식, 손상 여부와 픽셀 수 검사
        validated_image = image_validator.validate_upload(
            image_bytes=image_bytes,
            declared_mime_type=declared_mime_type,
        )

    except ImageValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    try:
        # 세션 UUID를 기준으로 원본 파일 저장
        _, original_image_url = image_storage.save_original(
            generation_id=session_id,
            source=BytesIO(image_bytes),
            extension=validated_image.extension,
        )

    except (OSError, ValueError) as error:
        # 저장 도중 만들어진 일부 파일과 폴더 정리
        image_storage.delete_original(session_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="원본 이미지를 저장하지 못했습니다.",
        ) from error

    try:
        # 저장된 이미지 정보를 기획 세션 DB에 반영
        planning_session = (
            planning_session_service.attach_original_image(
                db=db,
                planning_session=planning_session,
                original_filename=original_filename,
                original_image_url=original_image_url,
                original_mime_type=validated_image.mime_type,
                original_file_size=validated_image.file_size,
            )
        )

    except RuntimeError as error:
        # DB 저장 실패 시 파일만 남지 않도록 정리
        image_storage.delete_original(session_id)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    return planning_session

# 최종 광고 세션 저장 및 확정
@router.post(
    "/{session_id}/confirm",
    response_model = PlanningSessionResponse,
    status_code=status.HTTP_200_OK,
)
def confirm_planning_session(
    session_id: UUID,
    confirm_request: PlanningSessionConfirmRequest,
    db: Annotated[
        Session,
        Depends(get_db)
    ]
) -> PlanningSession:
    # 최종 광고 기획서로 확정할 세션 조회
    try:
        planning_session = planning_session_service.get_session(
            db = db,
            session_id = session_id
        )
    except RuntimeError as error:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = str(error)
        ) from error

    if planning_session is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "광고 기획 세션을 찾을 수 없습니다."
        )

    # planning 상태인 세션만 -> 확정
    if planning_session.status != PlanningSessionStatus.PLANNING.value:
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = "이미 확정 되었거나 확정할 수 없는 기획 세션입니다."
        ) 

    # 광고 생성에 사용할 원본 이미지가 먼저 등록되어야 함
    if planning_session.original_image_url is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="기획서를 확정하기 전에 원본 이미지를 등록해야 합니다.",
        )

    try:
        return planning_session_service.confirm_session(
            db=db,
            planning_session=planning_session,
            confirm_request=confirm_request,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

