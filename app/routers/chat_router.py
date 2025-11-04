from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.services import chat_service
from app.services import chat_group_service
from app.schemas.chat_schemas import (
    GroupCreateRequest,
    AddGroupMembersRequest,
    UpdateGroupTitleRequest,
    ChatResponse,
    GroupMemberResponse
)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


# Chat service routes
@router.get("", response_model=List[ChatResponse])
async def get_user_chats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить список всех чатов текущего пользователя"""
    chats = await chat_service.get_user_chats(db, current_user.id)
    return chats


@router.post("/private/{friend_id}", status_code=status.HTTP_201_CREATED, response_model=ChatResponse)
async def get_or_create_private_chat(
    friend_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать или получить приватный чат с другом"""
    chat = await chat_service.get_or_create_private_chat(db, current_user.id, friend_id)
    return chat


# Group chat service routes
@router.post("/group", status_code=status.HTTP_201_CREATED, response_model=ChatResponse)
async def create_group(
    group_data: GroupCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать новую группу"""
    if not group_data.title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group title cannot be empty"
        )

    chat = await chat_group_service.create_group_chat(
        db=db,
        group_title=group_data.title,
        creator_id=current_user.id,
        friend_ids=group_data.friend_ids
    )
    
    return chat


@router.post("/group/{chat_id}/members", response_model=dict)
async def add_group_members(
    chat_id: int,
    members_data: AddGroupMembersRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Добавить участников в группу"""
    added_ids = await chat_group_service.add_group_members(
        db=db,
        chat_id=chat_id,
        added_by=current_user.id,
        friend_ids=members_data.friend_ids
    )
    return {"added_user_ids": added_ids}


@router.get("/group/{chat_id}/members", response_model=List[GroupMemberResponse])
async def get_group_members(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить список участников группы"""
    members = await chat_group_service.get_group_members(db, chat_id, current_user.id)
    return members


@router.delete("/group/{chat_id}/members/{user_id}", status_code=status.HTTP_200_OK, response_model=dict)
async def delete_group_member(
    chat_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить участника из группы (только для админов и создателя)"""
    result = await chat_group_service.delete_group_member(
        db=db,
        chat_id=chat_id,
        user_id=user_id,
        removed_by=current_user.id
    )
    return result


@router.post("/group/{chat_id}/leave", status_code=status.HTTP_200_OK, response_model=dict)
async def leave_group(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Покинуть группу"""
    result = await chat_group_service.leave_group(
        db=db,
        chat_id=chat_id,
        user_id=current_user.id
    )
    return result


@router.post("/group/{chat_id}/promote/{user_id}", status_code=status.HTTP_200_OK, response_model=dict)
async def promote_to_admin(
    chat_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Повысить участника до админа (только для админов и создателя)"""
    result = await chat_group_service.promote_to_admin(
        db=db,
        chat_id=chat_id,
        target_user_id=user_id,
        requested_by=current_user.id
    )
    return result


@router.post("/group/{chat_id}/demote/{user_id}", status_code=status.HTTP_200_OK, response_model=dict)
async def demote_to_participant(
    chat_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Понизить админа до участника (только для создателя)"""
    result = await chat_group_service.demote_to_participant(
        db=db,
        chat_id=chat_id,
        target_user_id=user_id,
        requested_by=current_user.id
    )
    return result


@router.put("/group/{chat_id}/title", status_code=status.HTTP_200_OK, response_model=dict)
async def update_group_title(
    chat_id: int,
    title_data: UpdateGroupTitleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить название группы (только для админов и создателя)"""
    result = await chat_group_service.update_group_title(
        db=db,
        chat_id=chat_id,
        new_title=title_data.title,
        updated_by=current_user.id
    )
    return result

