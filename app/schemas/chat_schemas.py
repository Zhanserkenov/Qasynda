from pydantic import BaseModel
from typing import List, Optional


class GroupCreateRequest(BaseModel):
    title: str
    friend_ids: Optional[List[int]] = None


