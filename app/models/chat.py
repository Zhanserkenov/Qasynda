from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base

class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    is_group = Column(Boolean, default=False, nullable=False)

    event = relationship("Event", back_populates="chat", uselist=False)
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    participants = relationship("ChatParticipant", back_populates="chat", cascade="all, delete-orphan")