from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .env의 DB 접속 정보 읽기
    db_host : str
    db_port : int = 5432
    db_user : str
    db_password : str
    db_name : str

    # 이미지 파일이 저장되는 폴더 경로 설정
    image_storage_dir: Path = Path("Image")

    # 저장된 이미지를 React에서 제공할때 사용할 FastAPI URL 시작 경로
    image_url_prefix: str = "/images"

    # 이미지 생성 완료 후, 사용자의 원본 이미지 저장 여부 (True: 저장, False: 저장 안함)
    keep_original_images: bool

    # 업로드 가능한 이미지 한 장의 최대 용량(MB)
    max_upload_image_size_mb: int

    model_grpc_target: str = "127.0.0.1:50051"      # 모델 서버가 실행되는 주소
    model_timeout_seconds: float = 120.0
    model_grpc_max_message_size_mb: int = 32       # gRPC에서 송수신할 수 있는 최대 메시지 크기(MiB)

    # .env파일을 utf-8형식으로 읽기
    model_config = SettingsConfigDict(
        env_file = '.env',
        env_file_encoding='utf-8',
        extra = 'ignore'
    )

# @lru_cache, Least Recently Used
# 최초 호출 시 .env로 settings를 만들고 캐시에 저장
@lru_cache
def get_settings() -> Settings:
    # get_setting은 Settings를 반환
    return Settings()