from sqlalchemy import Column, Integer, String, Enum as SqlEnum

from app.core.database import Base
from app.models.enums import UserRole


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    last_name = Column(String)
    password = Column(String)
    role = Column(SqlEnum(UserRole), default=UserRole.USER, nullable=False)
    photo_url = Column(String)
    bio = Column(String(150))