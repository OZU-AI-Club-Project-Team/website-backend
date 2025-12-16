from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ApplicationStatus(str, Enum):
    PENDING = "PENDING"
    CONTACTED = "CONTACTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class ApplicationType(str, Enum):
    IDEA = "IDEA"
    TEAM_MEMBER = "TEAM_MEMBER"


class WorkArea(str, Enum):
    FRONTEND = "FRONTEND"
    BACKEND = "BACKEND"
    DESIGN = "DESIGN"
    MOBILE = "MOBILE"
    MANAGEMENT = "MANAGEMENT"


# Nested models for application detail
class UserBasic(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    surname: Optional[str] = None
    teamMember: bool


class ApplicationFeedbackBasic(BaseModel):
    content: str
    accepted: bool


class ApplicationFeedbackDetail(BaseModel):
    content: str
    accepted: bool
    user: UserBasic
    date: datetime


class ApplicationDetailContent(BaseModel):
    """For IDEA applications: title/description populated.
    For TEAM_MEMBER applications: workAreas/bio/expectations/portfolioURL populated."""
    title: Optional[str] = None
    description: Optional[str] = None
    workAreas: Optional[List[WorkArea]] = None
    bio: Optional[str] = None
    expectations: Optional[str] = None
    portfolioURL: Optional[str] = None


# Response models
class ApplicationListItem(BaseModel):
    id: int
    email: EmailStr
    type: ApplicationType
    status: ApplicationStatus
    isRead: bool
    date: datetime
    feedback: Optional[ApplicationFeedbackBasic] = None


class ApplicationDetail(BaseModel):
    owner: UserBasic
    type: ApplicationType
    status: ApplicationStatus
    isRead: bool
    date: datetime
    detail: ApplicationDetailContent
    feedback: Optional[ApplicationFeedbackDetail] = None

