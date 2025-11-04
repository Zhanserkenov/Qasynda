from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models import Message, ChatParticipant, Chat


async def ensure_chat_member(db: AsyncSession, chat_id: int, user_id: int):
    """Проверяет, что пользователь является участником чата"""
    result = await db.execute(
        select(ChatParticipant).where(
            (ChatParticipant.chat_id == chat_id) & (ChatParticipant.user_id == user_id)
        )
    )
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this chat"
        )

    return participant


async def ensure_chat_exists(db: AsyncSession, chat_id: int):
    """Проверяет, что чат существует"""
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    return chat


async def send_message(
    db: AsyncSession,
    chat_id: int,
    sender_id: int,
    content: str
):
    """Отправить сообщение в чат"""
    # Проверяем, что чат существует
    await ensure_chat_exists(db, chat_id)

    # Проверяем, что отправитель является участником чата
    await ensure_chat_member(db, chat_id, sender_id)

    # Проверяем, что контент не пустой
    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty"
        )

    # Создаем сообщение
    message = Message(
        chat_id=chat_id,
        sender_id=sender_id,
        content=content.strip()
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    return message


async def get_chat_messages(
    db: AsyncSession,
    chat_id: int,
    user_id: int,
    skip: int = 0,
    limit: int = 50
):
    """Получить сообщения чата с пагинацией"""
    # Проверяем, что чат существует
    await ensure_chat_exists(db, chat_id)

    # Проверяем, что пользователь является участником чата
    await ensure_chat_member(db, chat_id, user_id)

    # Получаем общее количество сообщений
    total_result = await db.execute(
        select(func.count(Message.id)).where(Message.chat_id == chat_id)
    )
    total = total_result.scalar() or 0

    # Получаем сообщения с пагинацией, сортировка по дате создания (новые сначала)
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()

    # Переворачиваем список, чтобы старые сообщения были первыми
    messages = list(reversed(messages))

    return {
        "messages": messages,
        "total": total,
        "skip": skip,
        "limit": limit
    }


async def get_message(
    db: AsyncSession,
    message_id: int,
    user_id: int
):
    """Получить одно сообщение по ID"""
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Проверяем, что пользователь является участником чата
    await ensure_chat_member(db, message.chat_id, user_id)

    return message


async def update_message(
    db: AsyncSession,
    message_id: int,
    user_id: int,
    new_content: str
):
    """Обновить сообщение (только отправитель)"""
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Проверяем, что пользователь является отправителем
    if message.sender_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own messages"
        )

    # Проверяем, что новый контент не пустой
    if not new_content or not new_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty"
        )

    # Обновляем сообщение
    message.content = new_content.strip()
    db.add(message)
    await db.commit()
    await db.refresh(message)

    return message


async def delete_message(
    db: AsyncSession,
    message_id: int,
    user_id: int
):
    """Удалить сообщение (только отправитель)"""
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Проверяем, что пользователь является отправителем
    if message.sender_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own messages"
        )

    await db.delete(message)
    await db.commit()

    return {"message": "Message deleted successfully"}
