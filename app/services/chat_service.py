from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import select

from app.models import ChatParticipant, Chat, User

async def get_user_chats(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Chat)
        .join(ChatParticipant)
        .where(ChatParticipant.user_id == user_id)
        .order_by(Chat.id.desc())
    )
    chats = result.scalars().unique().all()

    if not chats:
        return []

    for chat in chats:
        if not chat.is_group:
            result = await db.execute(
                select(User)
                .join(ChatParticipant)
                .where(
                    ChatParticipant.chat_id == chat.id,
                    ChatParticipant.user_id != user_id
                )
            )
            other_user = result.scalar_one_or_none()
            if other_user:
                chat.title = other_user.username

    return chats

async def get_or_create_private_chat(db: AsyncSession, user_id: int, friend_id: int):
    if user_id == friend_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create private chat with yourself"
        )

    result = await db.execute(
        select(Chat)
        .join(ChatParticipant)
        .where(
            Chat.is_group == False,
            ChatParticipant.user_id.in_([user_id, friend_id])
        )
        .group_by(Chat.id)
        .having(db.func.count(ChatParticipant.user_id) == 2)
    )
    existing_chat = result.scalar_one_or_none()

    if existing_chat:
        return existing_chat

    new_chat = Chat(is_group=False)
    db.add(new_chat)
    await db.flush()
    await db.refresh(new_chat)

    db.add_all([
        ChatParticipant(chat_id=new_chat.id, user_id=user_id),
        ChatParticipant(chat_id=new_chat.id, user_id=friend_id)
    ])

    await db.commit()
    await db.refresh(new_chat)

    return new_chat