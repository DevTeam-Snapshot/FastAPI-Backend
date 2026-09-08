from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .env의 DB 접속 정보 읽기
    db_host : str
    db_port : int = 5432
    db_user : str
    db_password : str
    db_name : str

    model_grpc_target: str = "127.0.0.1:15051"      # 모델 서버가 실행되는 주소
    model_name: str = "Qwen/Qwen3-0.6B"             # 모델 명
    model_revision: str = (                         # 모델 서버와 백엔드가 같은 토크나이저 사용
        "c1899de289a04d12100db370d81485cdf75e47ca"
    )
    model_timeout_seconds: float = 120.0

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