from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .env의 DB 접속 정보 읽기
    db_host : str
    db_port : int = 3306
    db_user : str
    db_password : str
    db_name : str

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