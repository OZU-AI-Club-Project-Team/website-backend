# First Step: Complete Application Module

## Overview
Complete the Application module by implementing the missing endpoints according to the OpenAPI specification:
- `GET /application` - List all applications
- `GET /application/{id}` - Get application detail

## Step-by-Step Implementation

### Step 1: Create Application Schema File

**File:** `app/modules/application/application_schema.py`

**Create response models matching OpenAPI spec:**

```python
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
```

---

### Step 2: Implement Application List Endpoint

**File:** `app/modules/application/application_controller.py`

**Add function to get application list:**

```python
from fastapi import HTTPException, status
from app.db import db
from app.modules.application.application_schema import (
    ApplicationListItem,
    ApplicationDetail,
    ApplicationDetailContent,
    ApplicationFeedbackBasic,
    ApplicationFeedbackDetail,
    UserBasic,
)
from typing import List
from datetime import datetime


async def get_application_list() -> List[ApplicationListItem]:
    """
    Get list of all applications.
    Returns applications with basic information.
    """
    applications = await db.application.find_many(
        where={"deletedAt": None},
        include={
            "owner": True,
            "feedback": {
                "include": {
                    "user": True
                }
            }
        },
        order_by={"createdAt": "desc"}
    )
    
    result = []
    for app in applications:
        feedback_data = None
        if app.feedback:
            feedback_data = ApplicationFeedbackBasic(
                content=app.feedback.content,
                accepted=app.feedback.accepted
            )
        
        result.append(ApplicationListItem(
            id=app.id,
            email=app.owner.email,
            type=app.type,
            status=app.status,
            isRead=app.isRead,
            date=app.createdAt,
            feedback=feedback_data
        ))
    
    return result
```

---

### Step 3: Implement Application Detail Endpoint

**File:** `app/modules/application/application_controller.py`

**Add function to get application detail:**

```python
async def get_application_detail(application_id: int) -> ApplicationDetail:
    """
    Get detailed information about a specific application.
    """
    application = await db.application.find_unique(
        where={"id": application_id},
        include={
            "owner": True,
            "feedback": {
                "include": {
                    "user": True
                }
            },
            "ideaApplication": True,
            "teamMemberApplication": True
        }
    )
    
    if application is None or application.deletedAt is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Build owner info
    owner = UserBasic(
        id=application.owner.id,
        email=application.owner.email,
        name=application.owner.name,
        surname=application.owner.surname,
        teamMember=application.owner.teamMember is not None
    )
    
    # Build detail content based on application type
    detail_content = ApplicationDetailContent()
    
    if application.type == "IDEA" and application.ideaApplication:
        detail_content.title = application.ideaApplication.title
        detail_content.description = application.ideaApplication.description
    elif application.type == "TEAM_MEMBER" and application.teamMemberApplication:
        detail_content.workAreas = application.teamMemberApplication.workAreas
        detail_content.bio = application.teamMemberApplication.bio
        detail_content.expectations = application.teamMemberApplication.expectations
        detail_content.portfolioURL = application.teamMemberApplication.portfolioURL
    
    # Build feedback if exists
    feedback_detail = None
    if application.feedback:
        feedback_user = UserBasic(
            id=application.feedback.user.id,
            email=application.feedback.user.email,
            name=application.feedback.user.name,
            surname=application.feedback.user.surname,
            teamMember=application.feedback.user.teamMember is not None
        )
        feedback_detail = ApplicationFeedbackDetail(
            content=application.feedback.content,
            accepted=application.feedback.accepted,
            user=feedback_user,
            date=application.feedback.createdAt
        )
    
    return ApplicationDetail(
        owner=owner,
        type=application.type,
        status=application.status,
        isRead=application.isRead,
        date=application.createdAt,
        detail=detail_content,
        feedback=feedback_detail
    )
```

---

### Step 4: Update Application Router

**File:** `app/modules/application/application_router.py`

**Add new endpoints:**

```python
from fastapi import APIRouter, Path, Depends
from app.utils.security import require_roles
from app.modules.application import application_controller
from app.modules.application.application_schema import (
    ApplicationListItem,
    ApplicationDetail,
)
from typing import List

router = APIRouter(prefix="/application", tags=["application"])


@router.get("", response_model=List[ApplicationListItem])
async def get_application_list(current_user=Depends(require_roles("ADMIN"))):
    """
    Get list of all applications.
    Admin-only endpoint.
    """
    return await application_controller.get_application_list()


@router.get("/{id}", response_model=ApplicationDetail)
async def get_application_detail(
    id: int = Path(..., ge=1),
    current_user=Depends(require_roles("ADMIN"))
):
    """
    Get detailed information about a specific application.
    Admin-only endpoint.
    """
    return await application_controller.get_application_detail(id)


@router.patch("/{id}/mark-read")
async def mark_read(id: int = Path(..., ge=1), current_user=Depends(require_roles("ADMIN"))):
    return await application_controller.mark_read(id)
```

---

### Step 5: Update Application Module Init

**File:** `app/modules/application/__init__.py`

**Ensure router is exported:**

```python
from .application_router import router
```

---

### Step 6: Verify Router Registration

**File:** `app/routers/index.py`

**Check that application router is included** (should already be there):

```python
from app.modules.application import router as applicationRouter

# In setup_app function:
app.include_router(applicationRouter)
```

---

## Testing Checklist

After implementation, test:

- [ ] `GET /application` returns list of applications (admin only)
- [ ] `GET /application/{id}` returns application detail (admin only)
- [ ] Response format matches OpenAPI spec exactly
- [ ] IDEA applications show title/description in detail
- [ ] TEAM_MEMBER applications show workAreas/bio/expectations/portfolioURL in detail
- [ ] Feedback is included when present
- [ ] 404 error returned for non-existent applications
- [ ] Authorization works (non-admin users get 403)

---

## Notes

1. **Authorization:** Both endpoints are admin-only per OpenAPI spec. If you need different authorization, adjust accordingly.

2. **Soft Deletes:** The code filters out soft-deleted applications (`deletedAt is None`).

3. **Response Models:** Using Pydantic models ensures type safety and automatic OpenAPI documentation.

4. **Nested Relations:** Prisma's `include` is used to fetch related data in a single query.

5. **Type Handling:** The `detail` field structure differs based on `application.type` (IDEA vs TEAM_MEMBER).

---

## Next Steps After This

Once this is complete, you can:
1. Test thoroughly
2. Move to Phase 2: Implement Project Module
3. Follow the same pattern for remaining modules


