from pydantic import BaseModel
from datetime import datetime


class MessageCreateRequest(BaseModel):
    content: str


class MessageUpdateRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    total: int
    skip: int
    limit: int
