from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.services.chat_group_service import create_group_chat
from app.schemas.chat_schemas import GroupCreateRequest

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post("/group", status_code=status.HTTP_201_CREATED)
async def create_group(group_data: GroupCreateRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not group_data.title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group title cannot be empty"
        )

    chat = await create_group_chat(
        db=db,
        group_title=group_data.title,
        creator_id=current_user.id,
        friend_ids=group_data.friend_ids
    )
    
    return chat

