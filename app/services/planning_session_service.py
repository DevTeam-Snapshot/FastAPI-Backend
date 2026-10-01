from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.planning_session import PlanningSession
from app.models.enums import PlanningSessionStatus
from app.schemas.planning_session import PlanningSessionConfirmRequest

# 광고 기획 세션 생성 / 조회
class PlanningSessionService:
    # 광고 기획 세션 생성
    def create_session(
            self,
            db:Session,
    ) -> PlanningSession:
        planning_session = PlanningSession()

        db.add(planning_session)

        try:
            db.commit()

        except SQLAlchemyError as error:
            db.rollback()

            raise RuntimeError(
                "광고 기획 세션을 생성하지 못했습니다."
            ) from error

        db.refresh(planning_session)

        return planning_session

    # UUID에 해당 되는 광고 기획 세션 조회
    def get_session(
            self,
            db: Session,
            session_id : UUID
    ) -> PlanningSession | None:
        try:
            return db.get(
                PlanningSession,
                session_id
            )

        # 해당 UUID가 존재하지 않는 경우
        except SQLAlchemyError as error:
            raise RuntimeError(
                "해당 광고 기획 세션을 조회하지 못했습니다."
            ) from error

    # 기획 세션에 원본 이미지 정보 저장
    def attach_original_image(
            self,
            db: Session,
            planning_session: PlanningSession,
            original_filename: str,
            original_image_url: str,
            original_mime_type: str,
            original_file_size: int,
        ) -> PlanningSession:
            # 검증과 파일 저장을 마친 이미지 정보를 세션에 반영
            planning_session.original_filename = original_filename
            planning_session.original_image_url = original_image_url
            planning_session.original_mime_type = original_mime_type
            planning_session.original_file_size = original_file_size

            try: 
                db.commit()

            except SQLAlchemyError as error:
                db.rollback()

                raise RuntimeError(
                    "원본 이미지 정보를 저장하지 못했습니다."
                )
            
            db.refresh(planning_session)

            return planning_session

    # 완성된 광고 기획서 저장, 확정
    def confirm_session(
            self,
            db : Session,
            planning_session: PlanningSession,
            confirm_request: PlanningSessionConfirmRequest
    ) -> PlanningSession:
        # 최종 기획서 정보를 세션에 반영
        planning_session.lodging_type = (           # 숙소 유형
            confirm_request.lodging_type.value
        )

        planning_session.lodging_type_detail = (    # 기타 숙소 유형
            confirm_request.lodging_type_detail
        )

        planning_session.lodging_name = (           # 숙소 이름
            confirm_request.lodging_name
        )
    
        planning_session.location = (               # 숙소 위치
            confirm_request.location
        )

        planning_session.selling_points = (         # 공간 특징
            confirm_request.selling_points
        )

        planning_session.lodging_service = (        # 서비스와 혜택
            confirm_request.lodging_service
        )

        planning_session.mood = (                   # 분위기
            confirm_request.mood
        )

        planning_session.color_preference = (       # 선호 색상
            confirm_request.color_preference
        )

        planning_session.target_audience = (        # 광고 대상
            confirm_request.target_audience
        )

        planning_session.ad_copy = (                # 광고 문구
            confirm_request.ad_copy
        )

        # 기획서 작성 완료 상태와 확정 시각 기록
        planning_session.status = (
            PlanningSessionStatus.CONFIRMED.value
        )

        planning_session.confirmed_at = datetime.now(
            timezone.utc
        )

        try:
            db.commit()


        except SQLAlchemyError as error:
            db.rollback()

            raise RuntimeError(
                "광고 기획서를 저장하지 못했습니다."
            ) from error

        db.refresh(planning_session)

        return planning_session

# router.py에서 쓸 객체
planning_session_service = PlanningSessionService()