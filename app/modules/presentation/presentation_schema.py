from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


# Nested models for presentation detail
class IdeaBasic(BaseModel):
    id: int
    title: str


class UserBasic(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    surname: Optional[str] = None
    teamMember: bool


class FeedbackUserBasic(BaseModel):
    id: int
    name: Optional[str] = None
    surname: Optional[str] = None
    teamMember: bool


class PresentationFeedback(BaseModel):
    content: str
    user: FeedbackUserBasic
    date: datetime


# Response models
class PresentationListItem(BaseModel):
    id: int
    title: str
    date: datetime
    done: bool
    own: bool


class PresentationDetail(BaseModel):
    idea: IdeaBasic
    title: str
    summary: str
    date: datetime
    location: str
    done: bool
    owners: List[UserBasic]
    feedbacks: List[PresentationFeedback]

