# API 데이터의 형식과 유효성을 검사하는 기능
from pydantic import BaseModel, ConfigDict, Field

# Test item 테이블에 새로운 데이터 저장
class TestItemCreate(BaseModel):
    text: str = Field(
        min_length = 1,
        max_length = 255
    )

# Test Item 테이블의 데이터 조회 및 Response
class TestItemResponse(BaseModel):
    id : int
    text: str

    # SQLAlchemy 모델의 객체 속성을 읽어 응답데이터로 변환
    model_config = ConfigDict(from_attributes=True)