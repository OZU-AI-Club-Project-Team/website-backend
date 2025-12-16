from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ProjectStatus(str, Enum):
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"
    CANCELLED = "CANCELLED"


class WorkRole(str, Enum):
    BACKEND_DEVELOPER = "BACKEND_DEVELOPER"
    FRONTEND_DEVELOPER = "FRONTEND_DEVELOPER"
    MOBILE_DEVELOPER = "MOBILE_DEVELOPER"
    DESIGNER = "DESIGNER"
    PROJECT_MANAGER = "PROJECT_MANAGER"
    SUPERVISOR = "SUPERVISOR"
    IDEATOR = "IDEATOR"


# Nested models for project detail
class UserBasic(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    surname: Optional[str] = None
    teamMember: bool


class ProjectMemberDetail(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    surname: Optional[str] = None
    roles: List[WorkRole]
    teamMember: bool


# Response models
class ProjectListItem(BaseModel):
    id: int
    title: str
    date: datetime
    own: bool
    public: bool
    showcase: bool


class ProjectDetail(BaseModel):
    id: int
    title: str
    description: str
    status: ProjectStatus
    public: bool
    showcase: bool
    date: datetime
    leader: UserBasic
    members: List[ProjectMemberDetail]
    ideaId: Optional[int] = None

