# 업로드된 이미지 파일의 실제 내용을 검사하는 서비스

from dataclasses import dataclass
from io import BytesIO
from math import sqrt

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import get_settings

# Pillow를 통해 검사한 이미지 형식 및 시스템에서 허용할 형식
SUPPORTED_IMAGE_FORMATS = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp")
}

# 이미지 검증을 통과한 결과
@dataclass(frozen=True)
class ValidatedImage:
    mime_type: str
    extension: str
    width: int
    height: int
    file_size: int

# 모델에 전달할 정규화 이미지
@dataclass(frozen=True)
class NormalizedImage:
    image_bytes: bytes
    mime_type: str
    extension: str
    width: int
    height: int
    file_size: int    

# 이미지 검증 실패를 나타내는 서비스 예외
class ImageValidationError(ValueError):
    pass

class ImageValidator:
    def __init__(
            self,
            max_file_size_mb: int,
            max_upload_pixels: int,
            max_model_pixels: int
    ) -> None:
        # MB -> bytes 변환
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.max_file_size_mb = max_file_size_mb
        self.max_upload_pixels = max_upload_pixels
        self.max_model_pixels = max_model_pixels

    def validate_upload(
        self,
        image_bytes: bytes,
        declared_mime_type: str
    ) -> ValidatedImage:
        # 깡통 파일 차단
        if not image_bytes:
            raise ImageValidationError(
                "비어있는 이미지 파일은 업로드 할수 없습니다."
            )

        file_size = len(image_bytes)

        # .env에서 정한 최대 파일 용량
        if file_size > self.max_file_size:
            raise ImageValidationError(
                f"이미지 크기는 {self.max_file_size_mb}MB 이하여야 합니다."
            )

        # 이미지 타입 검사
        allowed_mime_types = {
            mime_type
            for mime_type, _ in SUPPORTED_IMAGE_FORMATS.values()
        }

        if declared_mime_type not in allowed_mime_types:
            raise ImageValidationError(
                "JPEG, PNG, WebP 이미지만 업로드할 수 있습니다."
            )

        try:
            # 파일명이나 확장자가 아닌 실제 byte 데이터로 이미지 열기
            with Image.open(BytesIO(image_bytes)) as image:
                actual_format = image.format

                if actual_format not in SUPPORTED_IMAGE_FORMATS:
                    raise ImageValidationError(
                        "JPEG, PNG, WebP 이미지만 업로드할 수 있습니다."
                    )

                actual_mime_type, extension = (
                    SUPPORTED_IMAGE_FORMATS[actual_format]
                )

                # 브라우저가 보낸 MIME 타입과 실제 파일 형식 비교
                if actual_mime_type != declared_mime_type:
                    raise ImageValidationError(
                        "이미지의 MIME 타입과 실제 파일 형식이 일치하지 않습니다."
                    )

                # 여러 프레임을 가진 움직이는 WebP 차단
                if getattr(image, "is_animated", False):
                    raise ImageValidationError(
                        "움직이는 WebP 이미지는 업로드할 수 없습니다."
                    )

                width, height = image.size

                if width <= 0 or height <= 0:
                    raise ImageValidationError(
                        "이미지의 가로 또는 세로 크기가 올바르지 않습니다."
                    )

                # 압축은 잘됐지만 해상도가 지나치게 큰 이미지 차단
                if width * height > self.max_upload_pixels:
                    raise ImageValidationError(
                        "이미지의 전체 픽셀 수가 허용 범위를 초과했습니다."
                    )

                # 이미지 데이터가 끝까지 정상적으로 구성됐는지 검사
                image.verify()

        except ImageValidationError:
            # 위에서 만든 구체적인 검증 메시지는 그대로 전달
            raise

        except (
            UnidentifiedImageError,
            Image.DecompressionBombError,
            OSError,
            SyntaxError,
            ValueError,
        ) as error:
            # Pillow가 열 수 없는 파일 또는 손상된 이미지
            raise ImageValidationError(
                "손상되었거나 올바르지 않은 이미지 파일입니다."
            ) from error

        return ValidatedImage(
            mime_type=actual_mime_type,
            extension=extension,
            width=width,
            height=height,
            file_size=file_size,
        )
    
    # 모델에 전달할 이미지 정규화
    def normalize_for_model(
        self,
        image_bytes: bytes,
        declared_mime_type: str,
    ) -> NormalizedImage:
        # 정규화 전에 업로드 이미지 검증
        self.validate_upload(
            image_bytes=image_bytes,
            declared_mime_type=declared_mime_type,
        )

        try:
            with Image.open(BytesIO(image_bytes)) as image:
                # 이미지 전체 데이터를 메모리에 불러오기
                image.load()

                # 스마트폰 사진 등의 EXIF 회전 정보 적용
                image = ImageOps.exif_transpose(image)

                width, height = image.size
                total_pixels = width * height

                # 모델 입력 기준보다 크면 비율을 유지하며 축소
                if total_pixels > self.max_model_pixels:
                    scale = sqrt(
                        self.max_model_pixels / total_pixels
                    )

                    resized_width = max(1, int(width * scale))
                    resized_height = max(1, int(height * scale))

                    image = image.resize(
                        (resized_width, resized_height),
                        Image.Resampling.LANCZOS,
                    )

                # 투명 영역을 흰색 배경과 합성
                if image.mode in {"RGBA", "LA"} or (
                    image.mode == "P"
                    and "transparency" in image.info
                ):
                    rgba_image = image.convert("RGBA")

                    background = Image.new(
                        "RGB",
                        rgba_image.size,
                        "white",
                    )

                    background.paste(
                        rgba_image,
                        mask=rgba_image.getchannel("A"),
                    )

                    image = background

                else:
                    image = image.convert("RGB")

                normalized_width, normalized_height = image.size

                output = BytesIO()

                # 모델 전송용 이미지는 JPEG로 통일
                image.save(
                    output,
                    format="JPEG",
                    quality=90,
                    optimize=True,
                )

                normalized_bytes = output.getvalue()

        except (
            UnidentifiedImageError,
            Image.DecompressionBombError,
            OSError,
            ValueError,
        ) as error:
            raise ImageValidationError(
                "모델 입력용 이미지로 변환하지 못했습니다."
            ) from error

        if len(normalized_bytes) > self.max_file_size:
            raise ImageValidationError(
                "정규화된 이미지의 크기가 허용 범위를 초과했습니다."
            )

        return NormalizedImage(
            image_bytes=normalized_bytes,
            mime_type="image/jpeg",
            extension=".jpg",
            width=normalized_width,
            height=normalized_height,
            file_size=len(normalized_bytes),
        )
settings = get_settings()

image_validator = ImageValidator(
    max_file_size_mb=settings.max_upload_image_size_mb,
    max_upload_pixels=settings.max_upload_image_pixels,
    max_model_pixels=settings.max_model_image_pixels
)