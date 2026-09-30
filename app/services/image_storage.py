# 이미지 저장소

from pathlib import Path
from shutil import copyfileobj
from typing import BinaryIO
from uuid import UUID

from app.core.config import get_settings

# 원본 이미지와 생성 이미지를 저장하는 클래스
class ImageStorage:
    def __init__(
            self,
            storage_dir: Path,
            url_prefix: str
    ) -> None:
        # 저장 경로 (상대 경로 -> 절대 경로)
        self.storage_dir = storage_dir.resolve()

        # URL 마지막에 /가 중복 되지 않도록 제거
        self.url_prefix = url_prefix.rstrip("/")

        # 입력 이미지와 결과 이미지 저장 경로
        self.requests_dir = self.storage_dir / "requests"
        self.results_dir = self.storage_dir / "results"

        # 폴더가 없으면 생성
        self.requests_dir.mkdir(parents = True, exist_ok=True)
        self.results_dir.mkdir(parents = True, exist_ok = True)

    # 원본 이미지 저장
    def save_original(
            self,
            generation_id: UUID,
            source: BinaryIO,
            extension: str,
    ) -> tuple[Path, str]:
        # 허용 되지 않은 확장자가 저장되는 것을 방지
        safe_extension = self._validate_extension(extension)

        # 요청 UUID별 저장 폴더 생성
        generation_dir = self.requests_dir / str(generation_id)
        generation_dir.mkdir(parents = True, exist_ok=True)

        # 원본 이미지가 저장될 경로
        file_path = generation_dir / f"original{safe_extension}"

        # 파일의 읽기 위치를 처음으로 이동
        source.seek(0)

        # 업로드 파일의 내용을 저장 파일로 복사
        with file_path.open("wb") as destination:
            copyfileobj(source, destination)

        # React에 넘길 원본 이미지 URL 생성
        image_url = (
            f"{self.url_prefix}/requests/"
            f"{generation_id}/original{safe_extension}"
        )

        return file_path, image_url

    # UUID에 해당하는 원본 이미지 읽기
    def read_original(
            self,
            generation_id: UUID
    ) -> bytes:
        generation_dir = (
            self.requests_dir / str(generation_id)
        )

        if not generation_dir.exists():
            raise FileNotFoundError(
                "원본 이미지 폴더를 찾을 수 없습니다."
            )

        original_files = [
            file_path
            for file_path in generation_dir.iterdir()
            if (
                file_path.is_file()
                and file_path.stem == "original"
                and file_path.suffix.lower()
                in {".jpg", ".jpeg", ".png", ".webp"}
            )
        ]

        if len(original_files) != 1:
            raise FileNotFoundError(
                "정확한 원본 이미지 파일을 찾을 수 없습니다."
            )

        return original_files[0].read_bytes()

        # UUID에 해당하는 원본 이미지가 정확히 한 개 있는지 확인
    def has_original(
        self,
        generation_id: UUID,
    ) -> bool:
        generation_dir = (
            self.requests_dir / str(generation_id)
        )

        if not generation_dir.is_dir():
            return False

        original_files = [
            file_path
            for file_path in generation_dir.iterdir()
            if (
                file_path.is_file()
                and file_path.stem == "original"
                and file_path.suffix.lower()
                in {".jpg", ".jpeg", ".png", ".webp"}
            )
        ]

        return len(original_files) == 1

    # 모델이 생성한 결과 이미지 저장
    def save_generated(
            self,
            generation_id: UUID,
            image_bytes: bytes,
            extension: str = ".png"
    ) -> tuple[Path, str]:
        safe_extension = self._validate_extension(extension)

        # 요청 UUID 별 폴더 생성
        generation_dir = self.results_dir / str(generation_id)
        generation_dir.mkdir(parents=True, exist_ok=True)

        # 생성 이미지가 저장될 실제 경로
        file_path = generation_dir / f"generated{safe_extension}"

        # 모델에서 전달 받은 이미지 byte 데이터를 파일로 저장
        file_path.write_bytes(image_bytes)

        # React에서 접근할 URL
        image_url = (
            f"{self.url_prefix}/results/"
            f"{generation_id}/generated{safe_extension}"
        )

        return file_path, image_url

    # UUID에 해당하는 생성 이미지 파일 경로 조회
    def get_generated_path(
            self,
            generation_id: UUID,
    ) -> Path:
        file_path = (
            self.results_dir
            / str(generation_id)
            / "generated.png"
        )

        if not file_path.is_file():
            raise FileNotFoundError(
                "생성된 광고 이미지 파일을 찾을 수 없습니다."
            )

        return file_path

    # 요청 UUID에 해당하는 원본 이미지 삭제
    def delete_original(
            self,
            generation_id: UUID
    ) -> None:
        # UUID를 이용해 삭제할 원본 이미지 폴더 지정
        generation_dir = self.requests_dir / str(generation_id)

        # 요청 폴더 안에 있는 원본 이미지 확인
        if generation_dir.exists():
            for file_path in generation_dir.iterdir():
                # 폴더 안의 파일만 삭제
                if file_path.is_file():
                    file_path.unlink()

            # 파일을 모두 삭제 하고 빈 폴더 삭제
            generation_dir.rmdir()

    # 요청 UUID에 해당되는 생성 이미지 삭제
    def delete_generated(
            self,
            generation_id: UUID
    ) -> None:
        # UUID에 해당되는 결과 이미지 폴더
        generation_dir = self.results_dir / str(generation_id)

        # 생성된 결과 이미지 폴더가 존재하는 경우에만 삭제
        if generation_dir.exists():
            for file_path in generation_dir.iterdir():
                # 해당 요청 폴더 안의 파일만 삭제
                if file_path.is_file():
                    file_path.unlink()

            # 파일 삭제 후 비어있는 UUID 폴더 삭제
            generation_dir.rmdir()

    # 이미지 확장자 검사
    def _validate_extension(self, extension: str) -> str:
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}

        normalized_extension = extension.lower()

        if normalized_extension not in allowed_extensions:
            raise ValueError("지원하지않는 이미지 확장자 입니다.\n(사용 가능 확장자: .jpg, .jpeg, .png, .webp)")

        return normalized_extension

# setting의 환경설정을 이용해 이미지 저장 객체 생성
settings = get_settings()

image_storage = ImageStorage(
    storage_dir = settings.image_storage_dir,
    url_prefix = settings.image_url_prefix
)
