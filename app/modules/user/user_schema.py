from enum import Enum
from pydantic import BaseModel


class UserRole(str, Enum):
    STUDENT = "STUDENT"
    MEMBER = "MEMBER"
    ADMIN = "ADMIN"


class User(BaseModel):
    id: int
    email: str
    role: UserRole
    key: str
