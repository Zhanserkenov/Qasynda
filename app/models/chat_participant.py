from sqlalchemy import Column, Integer, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import ChatParticipantRole


class ChatParticipant(Base):
    __tablename__ = 'chat_participants'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    role = Column(SqlEnum(ChatParticipantRole), default=ChatParticipantRole.PARTICIPANT, nullable=False)

    chat = relationship("Chat", back_populates="participants")
    user = relationship("User")