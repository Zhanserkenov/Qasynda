from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import ChatParticipant, Chat


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

