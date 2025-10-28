from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from passlib.context import CryptContext
import logging
from pydantic import EmailStr

from app.models import User

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def create_user(db: AsyncSession, email: EmailStr, password: str):

    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username or email already exists"
        )

    hashed_password = get_hash_password(password)

    user = User(email=str(email), password=hashed_password)

    logger.info("Adding user to database")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info(f"User created with ID: {user.id}")

    return user

async def login_user(db: AsyncSession, email: EmailStr, password: str):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )

    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )

    return user