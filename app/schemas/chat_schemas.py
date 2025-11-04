from pydantic import BaseModel
from typing import List, Optional


class GroupCreateRequest(BaseModel):
    title: str
    friend_ids: Optional[List[int]] = None


class AddGroupMembersRequest(BaseModel):
    friend_ids: List[int]


class UpdateGroupTitleRequest(BaseModel):
    title: str


class ChatResponse(BaseModel):
    id: int
    title: Optional[str]
    is_group: bool

    class Config:
        from_attributes = True


class GroupMemberResponse(BaseModel):
    id: int
    chat_id: int
    user_id: int
    role: str

    class Config:
        from_attributes = True


