from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    start_time = Column(DateTime)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"))

    chat = relationship("Chat", back_populates="event", uselist=False)
