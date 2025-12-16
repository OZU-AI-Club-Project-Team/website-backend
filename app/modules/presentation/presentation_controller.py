from fastapi import HTTPException, status
from app.db import db
from app.modules.presentation.presentation_schema import (
    PresentationListItem,
    PresentationDetail,
    IdeaBasic,
    UserBasic,
    FeedbackUserBasic,
    PresentationFeedback,
)
from typing import List, Optional


async def get_presentation_list(
    current: Optional[bool] = None,
    current_user_id: Optional[int] = None
) -> List[PresentationListItem]:
    """
    Get list of presentations.
    If current is True, returns only upcoming/current presentations (not yet done).
    If current_user_id is provided, calculates 'own' field.
    """
    # Build where clause
    where_clause = {"deletedAt": None}
    if current is True:
        where_clause["done"] = False
    
    presentations = await db.ideapresentation.find_many(
        where=where_clause,
        include={
            "idea": {
                "include": {
                    "owners": {
                        "include": {
                            "teamMember": True
                        }
                    }
                }
            }
        },
        order_by={"date": "asc"}
    )
    
    result = []
    for presentation in presentations:
        # Determine if current user is in the presenting team (idea owners)
        own = False
        if current_user_id is not None and presentation.idea:
            for owner in presentation.idea.owners:
                if owner.id == current_user_id:
                    own = True
                    break
        
        # Use idea title as presentation title (since title field may not exist in schema)
        title = presentation.idea.title if presentation.idea else "Presentation"
        
        result.append(PresentationListItem(
            id=presentation.id,
            title=title,
            date=presentation.date,
            done=presentation.done,
            own=own
        ))
    
    return result


async def get_presentation_detail(
    presentation_id: int,
    current_user_id: Optional[int] = None
) -> PresentationDetail:
    """
    Get detailed information about a specific presentation.
    """
    presentation = await db.ideapresentation.find_unique(
        where={"id": presentation_id},
        include={
            "idea": {
                "include": {
                    "owners": {
                        "include": {
                            "teamMember": True
                        }
                    }
                }
            },
            "feedbacks": {
                "include": {
                    "user": {
                        "include": {
                            "user": {
                                "include": {
                                    "teamMember": True
                                }
                            }
                        }
                    }
                }
            }
        }
    )
    
    if presentation is None or presentation.deletedAt is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentation not found"
        )
    
    if not presentation.idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found for this presentation"
        )
    
    # Build idea basic info
    idea = IdeaBasic(
        id=presentation.idea.id,
        title=presentation.idea.title
    )
    
    # Build owners list (from idea owners)
    owners = []
    for owner in presentation.idea.owners:
        owners.append(UserBasic(
            id=owner.id,
            email=owner.email,
            name=owner.name,
            surname=owner.surname,
            teamMember=owner.teamMember is not None
        ))
    
    # Build feedbacks list (only non-deleted ones)
    feedbacks = []
    for feedback in presentation.feedbacks:
        if feedback.deletedAt is None:
            # The feedback user is a TeamMember, so we need to get the User from it
            user = feedback.user.user if feedback.user else None
            if user:
                feedbacks.append(PresentationFeedback(
                    content=feedback.content,
                    user=FeedbackUserBasic(
                        id=user.id,
                        name=user.name,
                        surname=user.surname,
                        teamMember=user.teamMember is not None
                    ),
                    date=feedback.createdAt
                ))
    
    # Use idea title as presentation title (since title field may not exist in schema)
    title = presentation.idea.title
    
    return PresentationDetail(
        idea=idea,
        title=title,
        summary=presentation.summary,
        date=presentation.date,
        location=presentation.location,
        done=presentation.done,
        owners=owners,
        feedbacks=feedbacks
    )

