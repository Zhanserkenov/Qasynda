from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.services import message_service
from app.schemas.message_schemas import (
    MessageCreateRequest,
    MessageUpdateRequest,
    MessageResponse,
    MessageListResponse
)

router = APIRouter(
    prefix="/message",
    tags=["Message"]
)


@router.post("/chat/{chat_id}", status_code=status.HTTP_201_CREATED, response_model=MessageResponse)
async def send_message(
    chat_id: int,
    message_data: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отправить сообщение в чат"""
    message = await message_service.send_message(
        db=db,
        chat_id=chat_id,
        sender_id=current_user.id,
        content=message_data.content
    )
    return message


@router.get("/chat/{chat_id}", response_model=MessageListResponse)
async def get_chat_messages(
    chat_id: int,
    skip: int = Query(0, ge=0, description="Количество пропущенных сообщений"),
    limit: int = Query(50, ge=1, le=100, description="Максимальное количество сообщений"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить сообщения чата с пагинацией"""
    result = await message_service.get_chat_messages(
        db=db,
        chat_id=chat_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return result


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить одно сообщение по ID"""
    message = await message_service.get_message(
        db=db,
        message_id=message_id,
        user_id=current_user.id
    )
    return message


@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: int,
    message_data: MessageUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить сообщение (только отправитель)"""
    message = await message_service.update_message(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
        new_content=message_data.content
    )
    return message


@router.delete("/{message_id}", status_code=status.HTTP_200_OK)
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить сообщение (только отправитель)"""
    result = await message_service.delete_message(
        db=db,
        message_id=message_id,
        user_id=current_user.id
    )
    return result
