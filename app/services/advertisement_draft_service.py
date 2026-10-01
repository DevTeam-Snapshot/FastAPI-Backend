# A·B·C 광고 초안 생성 및 조회 서비스

from uuid import UUID

from sqlalchemy import case, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.advertisement_draft import AdvertisementDraft
from app.models.enums import (
    AdvertisementDraftStatus,
    DraftDirection,
    PlanningSessionStatus,
)
from app.models.planning_session import PlanningSession

# 같은 세션에 같은 회차가 이미 생성된 경우
class DraftRoundAlreadyExistsError(RuntimeError):
    pass

class DraftSelectionError(RuntimeError):
    pass

# 광고 초안을 다시 생성할 수 없는 경우
class DraftRegenerationError(RuntimeError):
    pass

class AdvertisementDraftService:
    # 3가지 초안 최초 생성 또는 실패한 1회차 초안 재시도 준비
    def create_initial_drafts(
            self,
            db: Session,
            planning_session: PlanningSession,
    ) -> list[AdvertisementDraft]:
        try:
            # 기존 1회차 초안 전체 조회
            drafts = list(
                db.scalars(
                    select(AdvertisementDraft).where(
                        AdvertisementDraft.session_id
                        == planning_session.id,
                        AdvertisementDraft.generation_round == 1,
                    )
                ).all()
            )

            # 기존 1회차 초안이 없는 경우 새로 생성
            if not drafts:
                drafts = [
                    AdvertisementDraft(
                        session_id=planning_session.id,
                        generation_round=1,
                        direction=direction.value,
                        status=AdvertisementDraftStatus.PENDING.value,
                    )
                    for direction in (
                        DraftDirection.ROOM,
                        DraftDirection.EMOTION,
                        DraftDirection.BENEFIT,
                    )
                ]

                db.add_all(drafts)

            # 기존 1회차 초안이 있는 경우 상태에 따라 처리
            else:
                if len(drafts) != 3:
                    raise DraftRoundAlreadyExistsError(
                        "1회차 광고 초안 데이터가 올바르지 않습니다."
                    )

                unfinished_statuses = {
                    AdvertisementDraftStatus.PENDING.value,
                    AdvertisementDraftStatus.PROCESSING.value,
                }

                # 이미 모델 호출이 진행 중이면 중복 요청 차단
                if any(
                    draft.status in unfinished_statuses
                    for draft in drafts
                ):
                    raise DraftRoundAlreadyExistsError(
                        "최초 광고 초안 생성이 이미 진행 중입니다."
                    )

                # 3개가 모두 성공했다면 최초 생성 재호출 차단
                if all(
                    draft.status
                    == AdvertisementDraftStatus.COMPLETED.value
                    for draft in drafts
                ):
                    raise DraftRoundAlreadyExistsError(
                        "최초 광고 초안 생성이 이미 완료되었습니다."
                    )

                # 실패한 초안만 같은 draft_id로 다시 시도
                for draft in drafts:
                    if (
                        draft.status
                        == AdvertisementDraftStatus.FAILED.value
                    ):
                        draft.status = (
                            AdvertisementDraftStatus.PENDING.value
                        )
                        draft.image_url = None
                        draft.file_size = None
                        draft.error_code = None
                        draft.error_message = None
                        draft.completed_at = None

            planning_session.status = (
                PlanningSessionStatus.GENERATING.value
            )

            db.commit()

        except DraftRoundAlreadyExistsError:
            db.rollback()
            raise

        except IntegrityError as error:
            db.rollback()

            raise DraftRoundAlreadyExistsError(
                "광고 초안이 이미 생성된 세션입니다."
            ) from error

        except SQLAlchemyError as error:
            db.rollback()

            raise RuntimeError(
                "광고 초안을 생성하지 못했습니다."
            ) from error

        for draft in drafts:
            db.refresh(draft)

        db.refresh(planning_session)

        return drafts
    
    # 2회차 광고 초안 재생성 준비
    def prepare_regeneration_drafts(
            self,
            db: Session,
            planning_session: PlanningSession
    ) -> list[AdvertisementDraft]:
        
        try:
            # 재생성에 이미 성공한 세션은 다시 요청할 수 없음
            if planning_session.regeneration_used:
                raise DraftRegenerationError(
                    "광고 초안 재생성 기회를 이미 사용했습니다."
                )

            # 최종 초안을 선택한 뒤에는 재생성할 수 없음
            selected_draft = db.scalar(
                select(AdvertisementDraft)
                .where(
                    AdvertisementDraft.session_id
                    == planning_session.id,
                    AdvertisementDraft.is_selected.is_(True),
                )
                .limit(1)
            )

            if selected_draft is not None:
                raise DraftRegenerationError(
                    "최종 초안을 선택한 뒤에는 다시 생성할 수 없습니다."
                )

            # 1회차 초안 조회
            initial_drafts = list(
                db.scalars(
                    select(AdvertisementDraft).where(
                        AdvertisementDraft.session_id
                        == planning_session.id,
                        AdvertisementDraft.generation_round == 1,
                    )
                ).all()
            )

            if len(initial_drafts) != 3:
                raise DraftRegenerationError(
                    "최초 광고 초안 3개가 생성된 후 다시 생성할 수 있습니다."
                )

            unfinished_statuses = {
                AdvertisementDraftStatus.PENDING.value,
                AdvertisementDraftStatus.PROCESSING.value,
            }

            # 1회차 모델 처리가 끝나야 재생성 가능
            if any(
                draft.status in unfinished_statuses
                for draft in initial_drafts
            ):
                raise DraftRegenerationError(
                    "최초 광고 초안의 생성 처리가 끝난 후 다시 생성할 수 있습니다."
                )

            # 1회차 초안이 모두 성공해야 사용자 재생성 가능
            if not all(
                draft.status
                == AdvertisementDraftStatus.COMPLETED.value
                for draft in initial_drafts
            ):
                raise DraftRegenerationError(
                    "실패한 최초 광고 초안을 먼저 다시 시도해야 합니다."
                )

            # 기존 2회차 초안 조회
            regeneration_drafts = list(
                db.scalars(
                    select(AdvertisementDraft).where(
                        AdvertisementDraft.session_id
                        == planning_session.id,
                        AdvertisementDraft.generation_round == 2,
                    )
                ).all()
            )

            if regeneration_drafts:
                # 이미 진행 중인 재생성 요청의 중복 실행 방지
                if any(
                    draft.status in unfinished_statuses
                    for draft in regeneration_drafts
                ):
                    raise DraftRegenerationError(
                        "광고 초안 재생성이 이미 진행 중입니다."
                    )

                # 세 초안이 모두 완료됐다면 재생성이 이미 성공한 상태
                if all(
                    draft.status
                    == AdvertisementDraftStatus.COMPLETED.value
                    for draft in regeneration_drafts
                ):
                    raise DraftRegenerationError(
                        "광고 초안 재생성이 이미 완료되었습니다."
                    )

                # 실패한 2회차 초안만 같은 draft_id로 재시도 준비
                for draft in regeneration_drafts:
                    if draft.status == AdvertisementDraftStatus.FAILED.value:
                        draft.status = (
                            AdvertisementDraftStatus.PENDING.value
                        )
                        draft.image_url = None
                        draft.file_size = None
                        draft.error_code = None
                        draft.error_message = None
                        draft.completed_at = None

            else:
                # 최초 재생성 요청이면 2회차 A·B·C 자리 생성
                regeneration_drafts = [
                    AdvertisementDraft(
                        session_id=planning_session.id,
                        generation_round=2,
                        direction=direction.value,
                        status=AdvertisementDraftStatus.PENDING.value,
                    )
                    for direction in (
                        DraftDirection.ROOM,
                        DraftDirection.EMOTION,
                        DraftDirection.BENEFIT,
                    )
                ]

                db.add_all(regeneration_drafts)

            planning_session.status = (
                PlanningSessionStatus.GENERATING.value
            )

            db.commit()

        except DraftRegenerationError:
            db.rollback()
            raise

        except IntegrityError as error:
            db.rollback()

            raise DraftRegenerationError(
                "2회차 광고 초안이 이미 생성된 세션입니다."
            ) from error

        except SQLAlchemyError as error:
            db.rollback()

            raise RuntimeError(
                "광고 초안 재생성을 준비하지 못했습니다."
            ) from error

        for draft in regeneration_drafts:
            db.refresh(draft)

        db.refresh(planning_session)

        # 전달 시 객실, 감성, 혜택 순서로 반환 하도록 설정
        direction_order = {
            DraftDirection.ROOM.value: 1,
            DraftDirection.EMOTION.value: 2,
            DraftDirection.BENEFIT.value: 3,
        }

        regeneration_drafts.sort(
            key=lambda draft: direction_order.get(
                draft.direction,
                4,
            )
        )

        return regeneration_drafts

    # 2회차 초안 3개가 모두 성공하면 재생성 기회 사용 처리
    def mark_regeneration_succeeded(
            self,
            db: Session,
            planning_session: PlanningSession,
    ) -> PlanningSession:
        try:
            # 이미 성공 처리된 요청은 같은 결과 반환
            if planning_session.regeneration_used:
                return planning_session

            regeneration_drafts = list(
                db.scalars(
                    select(AdvertisementDraft).where(
                        AdvertisementDraft.session_id
                        == planning_session.id,
                        AdvertisementDraft.generation_round == 2,
                    )
                ).all()
            )

            if len(regeneration_drafts) != 3:
                raise DraftRegenerationError(
                    "2회차 광고 초안 3개가 존재하지 않습니다."
                )

            # 세 초안이 모두 성공해야 재생성 기회를 사용한 것으로 처리
            if not all(
                draft.status
                == AdvertisementDraftStatus.COMPLETED.value
                for draft in regeneration_drafts
            ):
                raise DraftRegenerationError(
                    "2회차 광고 초안이 모두 완료되지 않았습니다."
                )

            planning_session.regeneration_used = True

            db.commit()

        except DraftRegenerationError:
            db.rollback()
            raise

        except SQLAlchemyError as error:
            db.rollback()

            raise RuntimeError(
                "광고 초안 재생성 성공 상태를 저장하지 못했습니다."
            ) from error

        db.refresh(planning_session)

        return planning_session
            

    # 한 세션의 모든 초안(3개) 조회
    def get_drafts(
            self,
            db: Session,
            session_id: UUID
    ) -> list[AdvertisementDraft]:
        # React에 항상 객실 -> 감성 -> 혜택 순서로 반환
        direction_order = case(
            (
                AdvertisementDraft.direction
                == DraftDirection.ROOM.value,
                1,
            ),
            (
                AdvertisementDraft.direction
                == DraftDirection.EMOTION.value,
                2,
            ),
            (
                AdvertisementDraft.direction
                == DraftDirection.BENEFIT.value,
                3,
            ),
            else_=4,
        )

        try:
            statement = (
                select(AdvertisementDraft)
                .where(
                    AdvertisementDraft.session_id == session_id
                )
                .order_by(
                    AdvertisementDraft.generation_round,
                    direction_order,
                )
            )

            return list(
                db.scalars(statement).all()
            )

        except SQLAlchemyError as error:
            raise RuntimeError(
                "광고 초안 목록을 조회하지 못했습니다."
            ) from error

    # 초안 1개 조회
    def get_draft(
            self,
            db: Session,
            session_id: UUID,
            draft_id: UUID
    ) -> AdvertisementDraft | None:
        try:
            statement = select(
                AdvertisementDraft
            ).where(
                AdvertisementDraft.id == draft_id,
                AdvertisementDraft.session_id == session_id
            )

            return db.scalar(statement)

        except SQLAlchemyError as error:
            raise RuntimeError(
                "해당 광고 초안을 조회하지 못했습니다."
            ) from error

    # draft_id로 광고 초안 한 개 조회
    def get_draft_by_id(
            self,
            db: Session,
            draft_id: UUID,
    ) -> AdvertisementDraft | None:
        try:
            return db.get(
                AdvertisementDraft,
                draft_id,
            )

        except SQLAlchemyError as error:
            raise RuntimeError(
                "광고 초안을 조회하지 못했습니다."
            ) from error

    # 완성된 광고 초안 한 개를 최종 선택
    def select_draft(
            self,
            db: Session,
            planning_session: PlanningSession,
            draft: AdvertisementDraft
    ) -> AdvertisementDraft:
        try:
            # 생성이 완료된 초안만 선택 가능
            if draft.status != AdvertisementDraftStatus.COMPLETED.value:
                raise DraftSelectionError(
                    "생성이 완료된 광고 초안만 선택할 수 있습니다."
                )

            # 재생성 성공 여부에 따라 현재 활성 회차 결정
            active_round = (
                2
                if planning_session.regeneration_used
                else 1
            )

            # 현재 활성화된 회차의 초안만 선택 가능
            if draft.generation_round != active_round:
                raise DraftSelectionError(
                    "현재 활성화된 광고 초안만 선택할 수 있습니다."
                )

            # 활성 회차 초안들의 생성 작업이 모두 끝났는지 확인
            active_drafts = list(
                db.scalars(
                    select(AdvertisementDraft).where(
                        AdvertisementDraft.session_id
                        == planning_session.id,
                        AdvertisementDraft.generation_round
                        == active_round,
                    )
                ).all()
            )

            unfinished_statuses = {
                AdvertisementDraftStatus.PENDING.value,
                AdvertisementDraftStatus.PROCESSING.value,
            }

            if any(
                active_draft.status in unfinished_statuses
                for active_draft in active_drafts
            ):
                raise DraftSelectionError(
                    "모든 광고 초안의 생성 처리가 끝난 후 선택할 수 있습니다."
                )

            # 같은 세션에서 이미 선택된 초안 확인
            selected_draft = db.scalar(
                select(AdvertisementDraft)
                .where(
                    AdvertisementDraft.session_id
                    == planning_session.id,
                    AdvertisementDraft.is_selected.is_(True),
                )
                .limit(1)
            )

            # 같은 초안을 다시 선택하면 기존 결과 반환
            if selected_draft is not None:
                if selected_draft.id == draft.id:
                    return selected_draft

                raise DraftSelectionError(
                    "이미 다른 광고 초안이 선택된 세션입니다."
                )

            # 최종 선택 상태 반영
            draft.is_selected = True
            planning_session.status = (
                PlanningSessionStatus.COMPLETED.value
            )

            db.commit()

        except DraftSelectionError:
            db.rollback()
            raise

        except SQLAlchemyError as error:
            db.rollback()

            raise RuntimeError(
                "광고 초안 선택 결과를 저장하지 못했습니다."
            ) from error

        db.refresh(draft)
        db.refresh(planning_session)

        return draft


advertisement_draft_service = AdvertisementDraftService()
