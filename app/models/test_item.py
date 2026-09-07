# 테이블에 사용할 SQLalchemy 자료 가져오기
from sqlalchemy import Integer, String

# Python -> SQL 연결
from sqlalchemy.orm import Mapped, mapped_column

# SQLalchemy 모델이 상속하는 공통 Base
from app.db.base import Base

# test_items 테이블 제작
class TestItem(Base):
    __tablename__ = "test_items"

    # id 칼럼
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key = True,
        autoincrement= True
    )

    # text 칼럼
    text : Mapped[str] = mapped_column(
        String(255),                    # 255자 이내의 값 (제목, 짧은 광고 문구에 적합)
        nullable = False
    )