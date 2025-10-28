from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import create_user, login_user
from app.core.database import get_db
from app.auth.schemas import UserSchema
from app.core.security import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserSchema, db: AsyncSession = Depends(get_db)):
    user = await create_user(db, user_data.email, user_data.password)

    return {
        "message": "User registered successfully",
        "user_id": user.id
    }

@router.post("/login")
async def login(user_data: UserSchema, db: AsyncSession = Depends(get_db)):
    user = await login_user(db, user_data.email, user_data.password)
    access_token = create_access_token({"sub": str(user.id), "role": user.role})

    return {
        "message": "User logged in",
        "access_token": access_token
    }