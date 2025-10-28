from enum import Enum

class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class FriendshipStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class ChatParticipantRole(str, Enum):
    CREATOR = "CREATOR"
    PARTICIPANT = "PARTICIPANT"
    ADMIN = "ADMIN"