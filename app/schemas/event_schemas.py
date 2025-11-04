from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class EventCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    participant_ids: Optional[List[int]] = None


class EventUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None


class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    creator_id: Optional[int]
    start_time: Optional[datetime]
    chat_id: int

    class Config:
        from_attributes = True


class ChatInfoResponse(BaseModel):
    id: int
    title: Optional[str]
    is_group: bool

    class Config:
        from_attributes = True


class EventWithChatResponse(BaseModel):
    event: EventResponse
    chat: ChatInfoResponse


class AddEventParticipantsRequest(BaseModel):
    participant_ids: List[int]
