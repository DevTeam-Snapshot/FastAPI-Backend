from fastapi import APIRouter, Depends, HTTPException, status

# SQLAlchemy 조회문과 DB 세션
from sqlalchemy import select
from sqlalchemy.orm import Session

# DB 세션, TestItem 모델, 통합 요청·응답 스키마
from app.db.session import get_db
from app.models.test_item import TestItem
from app.schemas.integration_test import (
    IntegrationTestRequest,
    IntegrationTestResponse
)
# 모델 클라이언트
from app.clients.model import model_client

# 통합 연동 테스트 API의 공통 주소와 Swagger 그룹 설정
router = APIRouter(
    prefix="/api/integration-test",
    tags=["Integration Test"]
)

# React의 질문과 index를 받아 모델 답변과 DB 값을 함께 반환
@router.post(
    "",
    response_model=IntegrationTestResponse,
    status_code=status.HTTP_200_OK
)
async def run_integration_test(
    request: IntegrationTestRequest,
    db: Session = Depends(get_db)
) -> IntegrationTestResponse:

    # React에서 받은 질문을 모델 클라이언트에 전달
    try:
        model_answer = await model_client.generate(
            request.question
        )

    except ConnectionError as error:
        raise HTTPException(
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
            detail = str(error)
        ) from error

    # React에서 받은 index와 동일한 id를 가진 레코드 조회
    statement = select(TestItem).where(
        TestItem.id == request.index
    )
    db_item = db.scalar(statement)

    # 해당 index의 데이터가 없으면 404 오류 반환
    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 index의 테스트 데이터가 없습니다."
        )

    # DB의 text와 모델 답변을 하나의 JSON 응답으로 구성
    return IntegrationTestResponse(
        index=request.index,
        db_text=db_item.text,
        model_answer=model_answer
    )