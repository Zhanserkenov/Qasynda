from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from typing import List, Optional
import random

from app.models import Chat, ChatParticipant
from app.models.enums import ChatParticipantRole
from app.services.friendship_service import get_friends

async def ensure_group_member(db: AsyncSession, chat_id: int, user_id: int):
    result = await db.execute(select(ChatParticipant).where((ChatParticipant.chat_id == chat_id)
                                                            & (ChatParticipant.user_id == user_id)))
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )

    return participant

async def ensure_group_chat(db: AsyncSession, chat_id: int):
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    if not chat.is_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This chat is not a group chat"
        )

    return chat

async def create_group_chat(db: AsyncSession, group_title: str, creator_id: int, friend_ids: Optional[List[int]] = None):
    if friend_ids is None:
        friend_ids = []

    create_chat = Chat(title=group_title, is_group=True)
    db.add(create_chat)
    await db.flush()
    await db.refresh(create_chat)

    creator_participant = ChatParticipant(
        chat_id=create_chat.id,
        user_id=creator_id,
        role=ChatParticipantRole.CREATOR
    )
    db.add(creator_participant)

    friends = await get_friends(db, creator_id)
    valid_friends_ids = {f.id for f in friends}

    valid_to_add = [fid for fid in friend_ids if fid in valid_friends_ids]
    if not valid_to_add:
        raise HTTPException(
            status_code=400,
            detail="You can only add your own friends"
        )

    for friend_id in valid_to_add:
        db.add(ChatParticipant(
            chat_id=create_chat.id,
            user_id=friend_id,
            role=ChatParticipantRole.PARTICIPANT
        ))

    await db.commit()
    
    return create_chat

async def add_group_members(db: AsyncSession, chat_id: int, added_by: int, friend_ids: Optional[List[int]] = None):
    await ensure_group_chat(db, chat_id)

    if not friend_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No friends provided"
        )

    await ensure_group_member(db, chat_id, added_by)

    friends = await get_friends(db, added_by)
    valid_friends_ids = {f.id for f in friends}

    valid_to_add = [fid for fid in friend_ids if fid in valid_friends_ids]
    if not valid_to_add:
        raise HTTPException(
            status_code=400,
            detail="You can only add your own friends"
        )

    result = await db.execute(select(ChatParticipant.user_id).where((ChatParticipant.chat_id == chat_id)
                                                            & (ChatParticipant.user_id.in_(valid_to_add))))
    already_in_group = set(result.scalars().all())
    to_add = [fid for fid in valid_to_add if fid not in already_in_group]

    if not to_add:
        raise HTTPException(
            status_code=400,
            detail="All selected users are already in the group"
        )

    for friend_id in to_add:
        db.add(ChatParticipant(
            chat_id=chat_id,
            user_id=friend_id,
            role=ChatParticipantRole.PARTICIPANT
        ))

    await db.commit()
    return to_add

async def get_group_members(db: AsyncSession, chat_id: int, viewer_id: int):
    await ensure_group_chat(db, chat_id)
    await ensure_group_member(db, chat_id, viewer_id)

    result = await db.execute(select(ChatParticipant).where(ChatParticipant.chat_id == chat_id))
    return result.scalars().all()

async def delete_group_member(db: AsyncSession, chat_id: int, user_id: int, removed_by: int):
    await ensure_group_chat(db, chat_id)

    result = await db.execute(select(ChatParticipant).where((ChatParticipant.chat_id == chat_id)
                                                            & (ChatParticipant.user_id == user_id)))
    target_participant = result.scalar_one_or_none()

    if not target_participant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this group"
        )

    remover_participant = await ensure_group_member(db, chat_id, removed_by)
    if remover_participant.role not in [ChatParticipantRole.ADMIN, ChatParticipantRole.CREATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group creator or admins are allowed to remove members"
        )

    if user_id == removed_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself from the group"
        )

    if target_participant.role in [ChatParticipantRole.ADMIN, ChatParticipantRole.CREATOR]:
        if remover_participant.role == ChatParticipantRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot remove creator/admin from the group"
            )

    await db.delete(target_participant)
    await db.commit()
    return {"removed_user_id": user_id}

async def leave_group(db: AsyncSession, chat_id: int, user_id: int):
    await ensure_group_chat(db, chat_id)

    participant = await ensure_group_member(db, chat_id, user_id)

    if participant.role == ChatParticipantRole.CREATOR:
        result = await db.execute(select(ChatParticipant).where((ChatParticipant.chat_id == chat_id)
                                                                & (ChatParticipant.user_id != user_id)))
        other_participants = result.scalars().all()

        if not other_participants:
            chat = await db.get(Chat, chat_id)
            await db.delete(participant)
            await db.delete(chat)
            await db.commit()
            return {"message": "You were the only member. Group deleted."}

        admins = [p for p in other_participants if p.role == ChatParticipantRole.ADMIN]
        if admins:
            new_creator = random.choice(admins)
        else:
            new_creator = random.choice(other_participants)

        new_creator.role = ChatParticipantRole.CREATOR

        await db.delete(participant)
        await db.commit()

        return {"message": f"You left the group. New creator is user {new_creator.user_id}"}

    await db.delete(participant)
    await db.commit()

    return {"message": "You have left the group"}

async def promote_to_admin(db: AsyncSession, chat_id: int, target_user_id: int, requested_by: int):
    await ensure_group_chat(db, chat_id)

    requester = await ensure_group_member(db, chat_id, requested_by)
    target = await ensure_group_member(db, chat_id, target_user_id)

    if requester.role not in [ChatParticipantRole.CREATOR, ChatParticipantRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only creator or admins can promote members"
        )

    if target.role == ChatParticipantRole.CREATOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change role of the creator"
        )

    if target.role == ChatParticipantRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already an admin"
        )

    target.role = ChatParticipantRole.ADMIN
    db.add(target)
    await db.commit()
    await db.refresh(target)

    return {"message": f"User {target_user_id} has been promoted to admin"}


async def demote_to_participant(db: AsyncSession, chat_id: int, target_user_id: int, requested_by: int):
    await ensure_group_chat(db, chat_id)

    requester = await ensure_group_member(db, chat_id, requested_by)
    target = await ensure_group_member(db, chat_id, target_user_id)

    if requester.role != ChatParticipantRole.CREATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group creator can demote admins"
        )

    if target.role == ChatParticipantRole.CREATOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot demote yourself as creator"
        )

    if target.role == ChatParticipantRole.PARTICIPANT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a participant"
        )

    target.role = ChatParticipantRole.PARTICIPANT
    db.add(target)
    await db.commit()
    await db.refresh(target)

    return {"message": f"User {target_user_id} has been demoted to participant"}

async def update_group_title(db: AsyncSession, chat_id: int, new_title: str, updated_by: int):
    chat = await ensure_group_chat(db, chat_id)

    participant = await ensure_group_member(db, chat_id, updated_by)

    if participant.role not in [ChatParticipantRole.ADMIN, ChatParticipantRole.CREATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group creator or admins can change the group title"
        )

    if not new_title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group title cannot be empty"
        )

    chat.title = new_title
    db.add(chat)
    await db.commit()
    await db.refresh(chat)

    return {"message": "Group title updated successfully", "new_title": chat.title}