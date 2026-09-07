from sqlalchemy.orm import DeclarativeBase

# 모든 DB모델이 상속할 공통 부모 클래스 생성 - > 데이터 베이스
class Base(DeclarativeBase):
    pass