from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.test_item import TestItem
from app.schemas.test_item import TestItemCreate, TestItemResponse

router = APIRouter(
    prefix = "/api/test-items",
    tags = ["Test Items"]
)

# 프론트엔드의 입력값을 데이터베이스에 저장
@router.post("",
             response_model = TestItemResponse,
             status_code = status.HTTP_201_CREATED)

def create_test_item(
    item: TestItemCreate,
    db: Session = Depends(get_db)
) -> TestItem:
    # 입력 데이터를 SQLAlchemy객체로 변환
    db_item = TestItem(text=item.text)

    # 새 객체를 DB에 등록
    db.add(db_item)
    db.commit()

    # DB가 생성한 id를 객체로 불러옴
    db.refresh(db_item)

    # JSON 형식으로 변환
    return db_item

# DB에 저장된 데이터를 id 순서대로 조회.
@router.get("",
            response_model = list[TestItemResponse]
)

def read_test_items(
    db: Session = Depends(get_db)
) -> list[TestItem]:
    # db를 테이블을 조회하고 오름차순으로 정렬
    statement = select(TestItem).order_by(TestItem.id)

    # SELECT, DB의 객체 목록을 가져옴
    items = db.scalars(statement).all()

    # JSON으로 반환
    return list(items)