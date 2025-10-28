from sqlalchemy import Column, Integer, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import FriendshipStatus


class Friendship(Base):
    __tablename__ = 'friendships'

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    status = Column(SqlEnum(FriendshipStatus), default=FriendshipStatus.PENDING)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])