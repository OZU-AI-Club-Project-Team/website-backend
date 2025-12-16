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


async def get_application_list() -> List[ApplicationListItem]:
    """
    Get list of all applications.
    Returns applications with basic information.
    """
    applications = await db.application.find_many(
        where={"deletedAt": None},
        include={
            "owner": {
                "include": {
                    "teamMember": True
                }
            },
            "feedback": {
                "include": {
                    "user": {
                        "include": {
                            "teamMember": True
                        }
                    }
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


async def get_application_detail(application_id: int) -> ApplicationDetail:
    """
    Get detailed information about a specific application.
    """
    application = await db.application.find_unique(
        where={"id": application_id},
        include={
            "owner": {
                "include": {
                    "teamMember": True
                }
            },
            "feedback": {
                "include": {
                    "user": {
                        "include": {
                            "teamMember": True
                        }
                    }
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


async def mark_read(application_id: int):
    app = await db.application.find_unique(where={"id": application_id})
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    await db.application.update(where={"id": application_id}, data={"isRead": True})
    return {"id": application_id, "isRead": True}
