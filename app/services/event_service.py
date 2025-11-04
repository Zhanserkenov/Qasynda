from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from typing import Optional, List
from datetime import datetime

from app.models import Event, Chat, ChatParticipant, User
from app.models.enums import ChatParticipantRole
from app.services.friendship_service import get_friends


async def create_event(
    db: AsyncSession,
    title: str,
    creator_id: int,
    description: Optional[str] = None,
    start_time: Optional[datetime] = None,
    participant_ids: Optional[List[int]] = None
):
    if not title or not title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event title cannot be empty"
        )

    if participant_ids is None:
        participant_ids = []

    event_chat = Chat(
        title=title.strip(),
        is_group=True
    )
    db.add(event_chat)
    await db.flush()
    await db.refresh(event_chat)

    creator_participant = ChatParticipant(
        chat_id=event_chat.id,
        user_id=creator_id,
        role=ChatParticipantRole.CREATOR
    )
    db.add(creator_participant)

    if participant_ids:
        friends = await get_friends(db, creator_id)
        valid_friends_ids = {f.id for f in friends}

        valid_to_add = [pid for pid in participant_ids if pid in valid_friends_ids]
        
        valid_to_add = [pid for pid in valid_to_add if pid != creator_id]

        if valid_to_add:
            for participant_id in valid_to_add:
                db.add(ChatParticipant(
                    chat_id=event_chat.id,
                    user_id=participant_id,
                    role=ChatParticipantRole.PARTICIPANT
                ))

    event = Event(
        title=title.strip(),
        description=description.strip() if description else None,
        creator_id=creator_id,
        start_time=start_time,
        chat_id=event_chat.id
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    await db.refresh(event_chat)

    return event


async def get_user_events(
    db: AsyncSession,
    user_id: int
):
    result = await db.execute(
        select(ChatParticipant.chat_id)
        .where(ChatParticipant.user_id == user_id)
    )
    chat_ids = [row[0] for row in result.all()]

    if not chat_ids:
        return []

    result = await db.execute(
        select(Event).where(Event.chat_id.in_(chat_ids)).order_by(Event.id.desc())
    )
    events = result.scalars().all()

    return events


async def get_event(
    db: AsyncSession,
    event_id: int,
    user_id: int
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    participant_result = await db.execute(
        select(ChatParticipant).where(
            (ChatParticipant.chat_id == event.chat_id) &
            (ChatParticipant.user_id == user_id)
        )
    )
    participant = participant_result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this event"
        )

    return event


async def update_event(
    db: AsyncSession,
    event_id: int,
    user_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    start_time: Optional[datetime] = None
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    participant_result = await db.execute(
        select(ChatParticipant).where(
            (ChatParticipant.chat_id == event.chat_id) &
            (ChatParticipant.user_id == user_id)
        )
    )
    participant = participant_result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this event"
        )

    if participant.role not in [ChatParticipantRole.CREATOR, ChatParticipantRole.ADMIN]:
        if event.creator_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only event creator or chat admins can update the event"
            )

    if title is not None:
        if not title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event title cannot be empty"
            )
        event.title = title.strip()
    
        chat_result = await db.execute(select(Chat).where(Chat.id == event.chat_id))
        chat = chat_result.scalar_one_or_none()
        if chat:
            chat.title = title.strip()
            db.add(chat)

    if description is not None:
        event.description = description.strip() if description else None

    if start_time is not None:
        event.start_time = start_time

    db.add(event)
    await db.commit()
    await db.refresh(event)

    return event


async def delete_event(
    db: AsyncSession,
    event_id: int,
    user_id: int
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    if event.creator_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only event creator can delete the event"
        )

    chat_id = event.chat_id

    await db.delete(event)
    
    chat_result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = chat_result.scalar_one_or_none()
    if chat:
        await db.delete(chat)
    
    await db.commit()

    return {"message": "Event and associated chat deleted successfully"}


async def add_event_participants(
    db: AsyncSession,
    event_id: int,
    added_by: int,
    participant_ids: List[int]
):
    if not participant_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No participants provided"
        )

    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    participant_result = await db.execute(
        select(ChatParticipant).where(
            (ChatParticipant.chat_id == event.chat_id) &
            (ChatParticipant.user_id == added_by)
        )
    )
    participant = participant_result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this event"
        )

    friends = await get_friends(db, added_by)
    valid_friends_ids = {f.id for f in friends}

    valid_to_add = [pid for pid in participant_ids if pid in valid_friends_ids]
    
    existing_result = await db.execute(
        select(ChatParticipant.user_id)
        .where(
            (ChatParticipant.chat_id == event.chat_id) &
            (ChatParticipant.user_id.in_(valid_to_add))
        )
    )
    already_participants = set(existing_result.scalars().all())
    to_add = [pid for pid in valid_to_add if pid not in already_participants]

    if not to_add:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All selected users are already participants of this event"
        )

    for participant_id in to_add:
        db.add(ChatParticipant(
            chat_id=event.chat_id,
            user_id=participant_id,
            role=ChatParticipantRole.PARTICIPANT
        ))

    await db.commit()
    return {"added_participant_ids": to_add}
