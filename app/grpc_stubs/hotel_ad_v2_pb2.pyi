from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LodgingType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LODGING_TYPE_UNSPECIFIED: _ClassVar[LodgingType]
    LODGING_TYPE_HOTEL: _ClassVar[LodgingType]
    LODGING_TYPE_MOTEL: _ClassVar[LodgingType]
    LODGING_TYPE_RESORT: _ClassVar[LodgingType]
    LODGING_TYPE_PENSION: _ClassVar[LodgingType]
    LODGING_TYPE_OTHER: _ClassVar[LodgingType]

class PlanningStep(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PLANNING_STEP_UNSPECIFIED: _ClassVar[PlanningStep]
    PLANNING_STEP_LODGING_TYPE: _ClassVar[PlanningStep]
    PLANNING_STEP_LODGING_INFORMATION: _ClassVar[PlanningStep]
    PLANNING_STEP_SELLING_POINTS: _ClassVar[PlanningStep]
    PLANNING_STEP_TARGET_AUDIENCE: _ClassVar[PlanningStep]
    PLANNING_STEP_MOOD: _ClassVar[PlanningStep]
    PLANNING_STEP_AD_COPY: _ClassVar[PlanningStep]
    PLANNING_STEP_COMPLETE: _ClassVar[PlanningStep]

class BriefField(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BRIEF_FIELD_UNSPECIFIED: _ClassVar[BriefField]
    BRIEF_FIELD_LODGING_TYPE: _ClassVar[BriefField]
    BRIEF_FIELD_LODGING_TYPE_DETAIL: _ClassVar[BriefField]
    BRIEF_FIELD_LODGING_NAME: _ClassVar[BriefField]
    BRIEF_FIELD_LOCATION: _ClassVar[BriefField]
    BRIEF_FIELD_SELLING_POINTS: _ClassVar[BriefField]
    BRIEF_FIELD_ORIGINAL_IMAGE: _ClassVar[BriefField]
    BRIEF_FIELD_TARGET_AUDIENCE: _ClassVar[BriefField]
    BRIEF_FIELD_MOOD: _ClassVar[BriefField]
    BRIEF_FIELD_COLOR_PREFERENCE: _ClassVar[BriefField]
    BRIEF_FIELD_AD_COPY: _ClassVar[BriefField]

class TurnEventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TURN_EVENT_TYPE_UNSPECIFIED: _ClassVar[TurnEventType]
    TURN_EVENT_TYPE_USER_MESSAGE: _ClassVar[TurnEventType]
    TURN_EVENT_TYPE_IMAGE_UPLOADED: _ClassVar[TurnEventType]

class MessageIntent(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MESSAGE_INTENT_UNSPECIFIED: _ClassVar[MessageIntent]
    MESSAGE_INTENT_ANSWER: _ClassVar[MessageIntent]
    MESSAGE_INTENT_CORRECTION: _ClassVar[MessageIntent]
    MESSAGE_INTENT_QUESTION: _ClassVar[MessageIntent]
    MESSAGE_INTENT_SYSTEM_EVENT: _ClassVar[MessageIntent]

class AnswerStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ANSWER_STATUS_UNSPECIFIED: _ClassVar[AnswerStatus]
    ANSWER_STATUS_VALID: _ClassVar[AnswerStatus]
    ANSWER_STATUS_AMBIGUOUS: _ClassVar[AnswerStatus]
    ANSWER_STATUS_OFF_TOPIC: _ClassVar[AnswerStatus]
    ANSWER_STATUS_NOT_APPLICABLE: _ClassVar[AnswerStatus]

class ConversationRole(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONVERSATION_ROLE_UNSPECIFIED: _ClassVar[ConversationRole]
    CONVERSATION_ROLE_USER: _ClassVar[ConversationRole]
    CONVERSATION_ROLE_ASSISTANT: _ClassVar[ConversationRole]

class DraftDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DRAFT_DIRECTION_UNSPECIFIED: _ClassVar[DraftDirection]
    DRAFT_DIRECTION_ROOM: _ClassVar[DraftDirection]
    DRAFT_DIRECTION_EMOTION: _ClassVar[DraftDirection]
    DRAFT_DIRECTION_BENEFIT: _ClassVar[DraftDirection]
LODGING_TYPE_UNSPECIFIED: LodgingType
LODGING_TYPE_HOTEL: LodgingType
LODGING_TYPE_MOTEL: LodgingType
LODGING_TYPE_RESORT: LodgingType
LODGING_TYPE_PENSION: LodgingType
LODGING_TYPE_OTHER: LodgingType
PLANNING_STEP_UNSPECIFIED: PlanningStep
PLANNING_STEP_LODGING_TYPE: PlanningStep
PLANNING_STEP_LODGING_INFORMATION: PlanningStep
PLANNING_STEP_SELLING_POINTS: PlanningStep
PLANNING_STEP_TARGET_AUDIENCE: PlanningStep
PLANNING_STEP_MOOD: PlanningStep
PLANNING_STEP_AD_COPY: PlanningStep
PLANNING_STEP_COMPLETE: PlanningStep
BRIEF_FIELD_UNSPECIFIED: BriefField
BRIEF_FIELD_LODGING_TYPE: BriefField
BRIEF_FIELD_LODGING_TYPE_DETAIL: BriefField
BRIEF_FIELD_LODGING_NAME: BriefField
BRIEF_FIELD_LOCATION: BriefField
BRIEF_FIELD_SELLING_POINTS: BriefField
BRIEF_FIELD_ORIGINAL_IMAGE: BriefField
BRIEF_FIELD_TARGET_AUDIENCE: BriefField
BRIEF_FIELD_MOOD: BriefField
BRIEF_FIELD_COLOR_PREFERENCE: BriefField
BRIEF_FIELD_AD_COPY: BriefField
TURN_EVENT_TYPE_UNSPECIFIED: TurnEventType
TURN_EVENT_TYPE_USER_MESSAGE: TurnEventType
TURN_EVENT_TYPE_IMAGE_UPLOADED: TurnEventType
MESSAGE_INTENT_UNSPECIFIED: MessageIntent
MESSAGE_INTENT_ANSWER: MessageIntent
MESSAGE_INTENT_CORRECTION: MessageIntent
MESSAGE_INTENT_QUESTION: MessageIntent
MESSAGE_INTENT_SYSTEM_EVENT: MessageIntent
ANSWER_STATUS_UNSPECIFIED: AnswerStatus
ANSWER_STATUS_VALID: AnswerStatus
ANSWER_STATUS_AMBIGUOUS: AnswerStatus
ANSWER_STATUS_OFF_TOPIC: AnswerStatus
ANSWER_STATUS_NOT_APPLICABLE: AnswerStatus
CONVERSATION_ROLE_UNSPECIFIED: ConversationRole
CONVERSATION_ROLE_USER: ConversationRole
CONVERSATION_ROLE_ASSISTANT: ConversationRole
DRAFT_DIRECTION_UNSPECIFIED: DraftDirection
DRAFT_DIRECTION_ROOM: DraftDirection
DRAFT_DIRECTION_EMOTION: DraftDirection
DRAFT_DIRECTION_BENEFIT: DraftDirection

class AdvertisementBrief(_message.Message):
    __slots__ = ("lodging_type", "lodging_type_detail", "lodging_name", "location", "selling_points", "target_audience", "mood", "color_preference", "ad_copy")
    LODGING_TYPE_FIELD_NUMBER: _ClassVar[int]
    LODGING_TYPE_DETAIL_FIELD_NUMBER: _ClassVar[int]
    LODGING_NAME_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    SELLING_POINTS_FIELD_NUMBER: _ClassVar[int]
    TARGET_AUDIENCE_FIELD_NUMBER: _ClassVar[int]
    MOOD_FIELD_NUMBER: _ClassVar[int]
    COLOR_PREFERENCE_FIELD_NUMBER: _ClassVar[int]
    AD_COPY_FIELD_NUMBER: _ClassVar[int]
    lodging_type: LodgingType
    lodging_type_detail: str
    lodging_name: str
    location: str
    selling_points: _containers.RepeatedScalarFieldContainer[str]
    target_audience: str
    mood: str
    color_preference: str
    ad_copy: str
    def __init__(self, lodging_type: _Optional[_Union[LodgingType, str]] = ..., lodging_type_detail: _Optional[str] = ..., lodging_name: _Optional[str] = ..., location: _Optional[str] = ..., selling_points: _Optional[_Iterable[str]] = ..., target_audience: _Optional[str] = ..., mood: _Optional[str] = ..., color_preference: _Optional[str] = ..., ad_copy: _Optional[str] = ...) -> None: ...

class StringChange(_message.Message):
    __slots__ = ("set_value", "clear")
    SET_VALUE_FIELD_NUMBER: _ClassVar[int]
    CLEAR_FIELD_NUMBER: _ClassVar[int]
    set_value: str
    clear: _empty_pb2.Empty
    def __init__(self, set_value: _Optional[str] = ..., clear: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ...) -> None: ...

class LodgingTypeChange(_message.Message):
    __slots__ = ("set_value", "clear")
    SET_VALUE_FIELD_NUMBER: _ClassVar[int]
    CLEAR_FIELD_NUMBER: _ClassVar[int]
    set_value: LodgingType
    clear: _empty_pb2.Empty
    def __init__(self, set_value: _Optional[_Union[LodgingType, str]] = ..., clear: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ...) -> None: ...

class StringListReplacement(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, values: _Optional[_Iterable[str]] = ...) -> None: ...

class BriefPatch(_message.Message):
    __slots__ = ("lodging_type", "lodging_type_detail", "lodging_name", "location", "selling_points", "target_audience", "mood", "color_preference", "ad_copy")
    LODGING_TYPE_FIELD_NUMBER: _ClassVar[int]
    LODGING_TYPE_DETAIL_FIELD_NUMBER: _ClassVar[int]
    LODGING_NAME_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    SELLING_POINTS_FIELD_NUMBER: _ClassVar[int]
    TARGET_AUDIENCE_FIELD_NUMBER: _ClassVar[int]
    MOOD_FIELD_NUMBER: _ClassVar[int]
    COLOR_PREFERENCE_FIELD_NUMBER: _ClassVar[int]
    AD_COPY_FIELD_NUMBER: _ClassVar[int]
    lodging_type: LodgingTypeChange
    lodging_type_detail: StringChange
    lodging_name: StringChange
    location: StringChange
    selling_points: StringListReplacement
    target_audience: StringChange
    mood: StringChange
    color_preference: StringChange
    ad_copy: StringChange
    def __init__(self, lodging_type: _Optional[_Union[LodgingTypeChange, _Mapping]] = ..., lodging_type_detail: _Optional[_Union[StringChange, _Mapping]] = ..., lodging_name: _Optional[_Union[StringChange, _Mapping]] = ..., location: _Optional[_Union[StringChange, _Mapping]] = ..., selling_points: _Optional[_Union[StringListReplacement, _Mapping]] = ..., target_audience: _Optional[_Union[StringChange, _Mapping]] = ..., mood: _Optional[_Union[StringChange, _Mapping]] = ..., color_preference: _Optional[_Union[StringChange, _Mapping]] = ..., ad_copy: _Optional[_Union[StringChange, _Mapping]] = ...) -> None: ...

class ConversationMessage(_message.Message):
    __slots__ = ("role", "content")
    ROLE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    role: ConversationRole
    content: str
    def __init__(self, role: _Optional[_Union[ConversationRole, str]] = ..., content: _Optional[str] = ...) -> None: ...

class ProcessTurnRequest(_message.Message):
    __slots__ = ("request_id", "session_id", "state_revision", "event_type", "user_message", "current_step", "brief", "original_image_uploaded", "fields_to_reconfirm", "resume_step", "ad_copy_candidates", "conversation_history")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    STATE_REVISION_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    USER_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_STEP_FIELD_NUMBER: _ClassVar[int]
    BRIEF_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_IMAGE_UPLOADED_FIELD_NUMBER: _ClassVar[int]
    FIELDS_TO_RECONFIRM_FIELD_NUMBER: _ClassVar[int]
    RESUME_STEP_FIELD_NUMBER: _ClassVar[int]
    AD_COPY_CANDIDATES_FIELD_NUMBER: _ClassVar[int]
    CONVERSATION_HISTORY_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    session_id: str
    state_revision: int
    event_type: TurnEventType
    user_message: str
    current_step: PlanningStep
    brief: AdvertisementBrief
    original_image_uploaded: bool
    fields_to_reconfirm: _containers.RepeatedScalarFieldContainer[BriefField]
    resume_step: PlanningStep
    ad_copy_candidates: _containers.RepeatedScalarFieldContainer[str]
    conversation_history: _containers.RepeatedCompositeFieldContainer[ConversationMessage]
    def __init__(self, request_id: _Optional[str] = ..., session_id: _Optional[str] = ..., state_revision: _Optional[int] = ..., event_type: _Optional[_Union[TurnEventType, str]] = ..., user_message: _Optional[str] = ..., current_step: _Optional[_Union[PlanningStep, str]] = ..., brief: _Optional[_Union[AdvertisementBrief, _Mapping]] = ..., original_image_uploaded: bool = ..., fields_to_reconfirm: _Optional[_Iterable[_Union[BriefField, str]]] = ..., resume_step: _Optional[_Union[PlanningStep, str]] = ..., ad_copy_candidates: _Optional[_Iterable[str]] = ..., conversation_history: _Optional[_Iterable[_Union[ConversationMessage, _Mapping]]] = ...) -> None: ...

class ProcessTurnResponse(_message.Message):
    __slots__ = ("request_id", "session_id", "state_revision", "message_intent", "answer_status", "assistant_message", "brief_updates", "corrected_fields", "fields_to_reconfirm", "completed_fields", "missing_fields", "current_step", "next_step", "resume_step", "ad_copy_candidates", "is_complete")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    STATE_REVISION_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_INTENT_FIELD_NUMBER: _ClassVar[int]
    ANSWER_STATUS_FIELD_NUMBER: _ClassVar[int]
    ASSISTANT_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    BRIEF_UPDATES_FIELD_NUMBER: _ClassVar[int]
    CORRECTED_FIELDS_FIELD_NUMBER: _ClassVar[int]
    FIELDS_TO_RECONFIRM_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_FIELDS_FIELD_NUMBER: _ClassVar[int]
    MISSING_FIELDS_FIELD_NUMBER: _ClassVar[int]
    CURRENT_STEP_FIELD_NUMBER: _ClassVar[int]
    NEXT_STEP_FIELD_NUMBER: _ClassVar[int]
    RESUME_STEP_FIELD_NUMBER: _ClassVar[int]
    AD_COPY_CANDIDATES_FIELD_NUMBER: _ClassVar[int]
    IS_COMPLETE_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    session_id: str
    state_revision: int
    message_intent: MessageIntent
    answer_status: AnswerStatus
    assistant_message: str
    brief_updates: BriefPatch
    corrected_fields: _containers.RepeatedScalarFieldContainer[BriefField]
    fields_to_reconfirm: _containers.RepeatedScalarFieldContainer[BriefField]
    completed_fields: _containers.RepeatedScalarFieldContainer[BriefField]
    missing_fields: _containers.RepeatedScalarFieldContainer[BriefField]
    current_step: PlanningStep
    next_step: PlanningStep
    resume_step: PlanningStep
    ad_copy_candidates: _containers.RepeatedScalarFieldContainer[str]
    is_complete: bool
    def __init__(self, request_id: _Optional[str] = ..., session_id: _Optional[str] = ..., state_revision: _Optional[int] = ..., message_intent: _Optional[_Union[MessageIntent, str]] = ..., answer_status: _Optional[_Union[AnswerStatus, str]] = ..., assistant_message: _Optional[str] = ..., brief_updates: _Optional[_Union[BriefPatch, _Mapping]] = ..., corrected_fields: _Optional[_Iterable[_Union[BriefField, str]]] = ..., fields_to_reconfirm: _Optional[_Iterable[_Union[BriefField, str]]] = ..., completed_fields: _Optional[_Iterable[_Union[BriefField, str]]] = ..., missing_fields: _Optional[_Iterable[_Union[BriefField, str]]] = ..., current_step: _Optional[_Union[PlanningStep, str]] = ..., next_step: _Optional[_Union[PlanningStep, str]] = ..., resume_step: _Optional[_Union[PlanningStep, str]] = ..., ad_copy_candidates: _Optional[_Iterable[str]] = ..., is_complete: bool = ...) -> None: ...

class GenerateDraftRequest(_message.Message):
    __slots__ = ("request_id", "session_id", "draft_id", "generation_round", "is_regeneration", "direction", "brief", "original_image_bytes", "image_mime_type")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    DRAFT_ID_FIELD_NUMBER: _ClassVar[int]
    GENERATION_ROUND_FIELD_NUMBER: _ClassVar[int]
    IS_REGENERATION_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    BRIEF_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_IMAGE_BYTES_FIELD_NUMBER: _ClassVar[int]
    IMAGE_MIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    session_id: str
    draft_id: str
    generation_round: int
    is_regeneration: bool
    direction: DraftDirection
    brief: AdvertisementBrief
    original_image_bytes: bytes
    image_mime_type: str
    def __init__(self, request_id: _Optional[str] = ..., session_id: _Optional[str] = ..., draft_id: _Optional[str] = ..., generation_round: _Optional[int] = ..., is_regeneration: bool = ..., direction: _Optional[_Union[DraftDirection, str]] = ..., brief: _Optional[_Union[AdvertisementBrief, _Mapping]] = ..., original_image_bytes: _Optional[bytes] = ..., image_mime_type: _Optional[str] = ...) -> None: ...

class GenerateDraftResponse(_message.Message):
    __slots__ = ("request_id", "session_id", "draft_id", "generation_round", "direction", "image_bytes", "image_mime_type")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    DRAFT_ID_FIELD_NUMBER: _ClassVar[int]
    GENERATION_ROUND_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    IMAGE_BYTES_FIELD_NUMBER: _ClassVar[int]
    IMAGE_MIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    session_id: str
    draft_id: str
    generation_round: int
    direction: DraftDirection
    image_bytes: bytes
    image_mime_type: str
    def __init__(self, request_id: _Optional[str] = ..., session_id: _Optional[str] = ..., draft_id: _Optional[str] = ..., generation_round: _Optional[int] = ..., direction: _Optional[_Union[DraftDirection, str]] = ..., image_bytes: _Optional[bytes] = ..., image_mime_type: _Optional[str] = ...) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("healthy",)
    HEALTHY_FIELD_NUMBER: _ClassVar[int]
    healthy: bool
    def __init__(self, healthy: bool = ...) -> None: ...

class ModelErrorDetail(_message.Message):
    __slots__ = ("request_id", "reason", "retryable")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    RETRYABLE_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    reason: str
    retryable: bool
    def __init__(self, request_id: _Optional[str] = ..., reason: _Optional[str] = ..., retryable: bool = ...) -> None: ...
