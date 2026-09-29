from enum import Enum

# 광고 기획 세션 전체 진행 상태 확인
class PlanningSessionStatus(str, Enum):
    PLANNING = "planning"
    CONFIRMED = "confirmed"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

# 사용자가 운영하는 숙소 유형
class LodgingType(str, Enum):
    HOTEL = "hotel"
    MOTEL = "motel"
    RESORT = "resort"
    PENSION = "pension"
    OTHER = "other"

# 광고 기획 진행 단계
class PlanningStep(str, Enum):
    LODGING_TYPE = "lodging_type"
    LODGING_INFORMATION = "lodging_information"
    SELLING_POINTS = "selling_points"
    LODGING_SERVICE = "lodging_service"
    MOOD = "mood"
    COLOR_PREFERENCE = "color_preference"
    TARGET_AUDIENCE = "target_audience"
    AD_COPY = "ad_copy"
    COMPLETE = "complete"

# A,B,C 광고 초안 생성 방향
class DraftDirection(str, Enum):
    ROOM = "room"           # 객실 중심 콘텐츠
    EMOTION = "emotion"     # 감성 중심 콘텐츠
    BENEFIT = "benefit"     # 혜택 중심 콘텐츠

# 광고 별 생성 상태
class AdvertisementDraftStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# 기획 대화에서 발생한 입력 유형
class TurnEventType(str, Enum):
    USER_MESSAGE = "user_message"
    IMAGE_UPLOADED = "image_uploaded"


# 사용자 메시지의 의도
class MessageIntent(str, Enum):
    ANSWER = "answer"
    CORRECTION = "correction"
    QUESTION = "question"
    SYSTEM_EVENT = "system_event"


# 사용자 답변의 판정 결과
class AnswerStatus(str, Enum):
    VALID = "valid"
    AMBIGUOUS = "ambiguous"
    OFF_TOPIC = "off_topic"
    NOT_APPLICABLE = "not_applicable"


# 모델에 전달하는 최근 대화의 역할
class ConversationRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


# 광고 기획서의 개별 필드
class BriefField(str, Enum):
    LODGING_TYPE = "lodging_type"
    LODGING_TYPE_DETAIL = "lodging_type_detail"
    LODGING_NAME = "lodging_name"
    LOCATION = "location"
    SELLING_POINTS = "selling_points"
    ORIGINAL_IMAGE = "original_image"
    LODGING_SERVICE = "lodging_service"
    MOOD = "mood"
    COLOR_PREFERENCE = "color_preference"
    TARGET_AUDIENCE = "target_audience"
    AD_COPY = "ad_copy"
