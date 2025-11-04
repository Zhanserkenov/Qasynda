from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Chat
from app.services import event_service
from app.schemas.event_schemas import (
    EventCreateRequest,
    EventUpdateRequest,
    EventResponse,
    AddEventParticipantsRequest,
    EventWithChatResponse,
    ChatInfoResponse
)

router = APIRouter(
    prefix="/event",
    tags=["Event"]
)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EventResponse)
async def create_event(
    event_data: EventCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    event = await event_service.create_event(
        db=db,
        title=event_data.title,
        creator_id=current_user.id,
        description=event_data.description,
        start_time=event_data.start_time,
        participant_ids=event_data.participant_ids
    )
    return event


@router.get("", response_model=List[EventResponse])
async def get_user_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    events = await event_service.get_user_events(db, current_user.id)
    return events


@router.get("/{event_id}", response_model=EventWithChatResponse)
async def get_event_with_chat(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    
    event = await event_service.get_event(db, event_id, current_user.id)
    
    chat_result = await db.execute(select(Chat).where(Chat.id == event.chat_id))
    chat = chat_result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat associated with event not found"
        )
    
    return EventWithChatResponse(
        event=EventResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            creator_id=event.creator_id,
            start_time=event.start_time,
            chat_id=event.chat_id
        ),
        chat=ChatInfoResponse(
            id=chat.id,
            title=chat.title,
            is_group=chat.is_group
        )
    )


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    event = await event_service.update_event(
        db=db,
        event_id=event_id,
        user_id=current_user.id,
        title=event_data.title,
        description=event_data.description,
        start_time=event_data.start_time
    )
    return event


@router.delete("/{event_id}", status_code=status.HTTP_200_OK)
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await event_service.delete_event(
        db=db,
        event_id=event_id,
        user_id=current_user.id
    )
    return result


@router.post("/{event_id}/participants", status_code=status.HTTP_200_OK)
async def add_event_participants(
    event_id: int,
    participants_data: AddEventParticipantsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await event_service.add_event_participants(
        db=db,
        event_id=event_id,
        added_by=current_user.id,
        participant_ids=participants_data.participant_ids
    )
    return result
