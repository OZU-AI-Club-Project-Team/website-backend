from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum


class IdeaStatus(str, Enum):
    DRAFT = "DRAFT"
    PRESENTED = "PRESENTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


# Nested models for idea detail
class UserBasic(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    surname: Optional[str] = None
    teamMember: bool


class PresentationBasic(BaseModel):
    id: int
    date: datetime
    done: bool


# Response models
class IdeaListItem(BaseModel):
    id: int
    title: str
    status: IdeaStatus
    date: datetime
    own: bool


class IdeaDetail(BaseModel):
    id: int
    title: str
    description: str
    status: IdeaStatus
    owners: List[UserBasic]
    teamMembers: List[UserBasic]
    presentations: List[PresentationBasic]
    applicationId: Optional[int] = None

