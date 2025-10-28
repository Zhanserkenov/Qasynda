from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Friendship
from app.models.enums import FriendshipStatus

async def send_request(db: AsyncSession, sender_id: int, receiver_id: int):
    if sender_id == receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't add yourself"
        )

    result = await db.execute(
        select(Friendship).where((Friendship.sender_id == sender_id) &
                                        (Friendship.receiver_id == receiver_id))
    )
    existing_request = result.scalar_one_or_none()

    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request already exists"
        )

    friendship = Friendship(sender_id=sender_id, receiver_id=receiver_id)
    db.add(friendship)
    await db.commit()
    await db.refresh(friendship)

    return friendship

async def update_request_status(db: AsyncSession, friendship_id: int, user_id: int, status_value: FriendshipStatus):
    result = await db.execute(select(Friendship).where(Friendship.id == friendship_id))
    friendship = result.scalar_one_or_none()

    if not friendship:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")

    if friendship.receiver_id != user_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "You cannot change this request"
        )

    friendship.status = status_value
    await db.commit()

    return friendship

async def get_incoming_requests(db: AsyncSession, user_id: int):
    result = await db.execute(select(Friendship).where((Friendship.status == FriendshipStatus.PENDING)
                                                       & (Friendship.receiver_id == user_id)))
    friendships = result.scalars().all()

    incoming_users = []
    for friendship in friendships:
        incoming_users.append(friendship.sender)

    return incoming_users

async def get_friends(db: AsyncSession, user_id: int):
    result = await db.execute(select(Friendship).where((Friendship.status == FriendshipStatus.ACCEPTED)
                                                       & ((Friendship.receiver_id == user_id)
                                                          | (Friendship.sender_id == user_id))))
    friendships = result.scalars().all()

    friends = []
    for friendship in friendships:
        if friendship.sender_id == user_id:
            friends.append(friendship.receiver)
        else:
            friends.append(friendship.sender)

    return friends

async def delete_friend(db: AsyncSession, friendship_id: int, user_id: int):
    result = await db.execute(select(Friendship).where(Friendship.id == friendship_id))
    friendship = result.scalar_one_or_none()

    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friendship not found"
        )

    if friendship.sender_id != user_id and friendship.receiver_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to remove this friend"
        )

    await db.delete(friendship)
    await db.commit()

    return {"message": "Friend deleted successfully"}