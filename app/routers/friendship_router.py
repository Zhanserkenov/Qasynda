from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.services.friendship_service import send_request, update_request_status, get_friends, get_incoming_requests, \
    delete_friend
from app.models.enums import FriendshipStatus

router = APIRouter(
    prefix="/friendship",
    tags=["Friendship"]
)

@router.post("/send/{receiver_id}", status_code=status.HTTP_201_CREATED)
async def friend_request(receiver_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await send_request(db, current_user.id, receiver_id)

@router.put("/accept/{friendship_id}")
async def accept_friend_request(friendship_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await update_request_status(db, friendship_id, current_user.id, FriendshipStatus.ACCEPTED)

@router.put("/reject/{friendship_id}")
async def reject_friend_request(friendship_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await update_request_status(db, friendship_id, current_user.id, FriendshipStatus.REJECTED)

@router.get("")
async def list_of_friends(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_friends(db, current_user.id)

@router.get("/incoming")
async def list_of_incoming_requests(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_incoming_requests(db, current_user.id)

@router.delete("/remove/{friendship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(friendship_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await delete_friend(db, friendship_id, current_user.id)