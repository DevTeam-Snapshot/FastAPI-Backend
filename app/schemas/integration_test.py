from pydantic import BaseModel, Field


# React가 FastAPI에 전달할 요청 데이터
class IntegrationTestRequest(BaseModel):
    # vLLM에 전달할 질문
    question: str = Field(
        min_length=1,
        max_length=1000
    )

    # DB에서 조회할 TestItem의 id
    index: int = Field(
        ge=1
    )

# FastAPI가 React에 반환할 응답 데이터
class IntegrationTestResponse(BaseModel):
    # React가 요청한 레코드 번호
    index: int

    # PostgreSQL에서 조회한 text
    db_text: str

    # 모델 서버에서 받은 답변
    model_answer: str