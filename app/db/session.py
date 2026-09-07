# session.py = DB연결 엔진과 세션 생성 방법을 관리

from collections.abc import Generator
from sqlalchemy.engine import URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import get_settings

# core에 저장한 setting값을 불러옴
settings = get_settings()

# PostgreSQL 접속에 사용할 주소 구성
database_url = URL.create(
    drivername = "postgresql+psycopg",
    username = settings.db_user,
    password = settings.db_password,
    host = settings.db_host,
    port = settings.db_port,
    database=settings.db_name
)

# SQLAlchemy가 PostgreSQL 연결을 관리할 엔진 생성 (연결 관리)
engine = create_engine(
    database_url,
    pool_pre_ping = True        # 연결이 되어있는지 간이 확인
)

# API 요청이 들어올 때 사용할 DB 세션 생성기
SessionLocal = sessionmaker(
    bind = engine,
    autoflush = False,
    autocommit = False
)

# API 요청마다 독립적인 DB세션 제공, 요청이 끝나면 세션 반납
def get_db() -> Generator[Session, None, None]:
    # SessionLocal을 호출해 사용할 세션을 생성
    db = SessionLocal()

    try:
        yield db            # DB 세션 전달

    finally:
        db.close()          # API 성공, 실패 여부와 관계없이 세션 닫기