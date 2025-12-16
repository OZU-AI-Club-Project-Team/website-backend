from fastapi import HTTPException, status
from app.db import db
from app.modules.idea.idea_schema import (
    IdeaListItem,
    IdeaDetail,
    UserBasic,
    PresentationBasic,
)
from typing import List, Optional


async def get_idea_list(
    current_user_id: Optional[int] = None
) -> List[IdeaListItem]:
    """
    Get list of ideas.
    If current_user_id is provided, calculates 'own' field.
    """
    ideas = await db.idea.find_many(
        where={"deletedAt": None},
        include={
            "owners": {
                "include": {
                    "teamMember": True
                }
            }
        },
        order_by={"createdAt": "desc"}
    )
    
    result = []
    for idea in ideas:
        # Determine if current user owns this idea
        own = False
        if current_user_id is not None:
            for owner in idea.owners:
                if owner.id == current_user_id:
                    own = True
                    break
        
        result.append(IdeaListItem(
            id=idea.id,
            title=idea.title,
            status=idea.status,
            date=idea.createdAt,
            own=own
        ))
    
    return result


async def get_idea_detail(
    idea_id: int,
    current_user_id: Optional[int] = None
) -> IdeaDetail:
    """
    Get detailed information about a specific idea.
    """
    idea = await db.idea.find_unique(
        where={"id": idea_id},
        include={
            "owners": {
                "include": {
                    "teamMember": True
                }
            },
            "presentations": True,
            "project": {
                "include": {
                    "members": {
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
    
    if idea is None or idea.deletedAt is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found"
        )
    
    # Build owners list
    owners = []
    for owner in idea.owners:
        owners.append(UserBasic(
            id=owner.id,
            email=owner.email,
            name=owner.name,
            surname=owner.surname,
            teamMember=owner.teamMember is not None
        ))
    
    # Build teamMembers list
    # Team members are project members who have TeamMember profiles
    team_members = []
    if idea.project and idea.project.members:
        for member in idea.project.members:
            if member.user.teamMember is not None:
                team_members.append(UserBasic(
                    id=member.user.id,
                    email=member.user.email,
                    name=member.user.name,
                    surname=member.user.surname,
                    teamMember=True
                ))
    
    # Build presentations list (only non-deleted ones)
    presentations = []
    for presentation in idea.presentations:
        if presentation.deletedAt is None:
            presentations.append(PresentationBasic(
                id=presentation.id,
                date=presentation.date,
                done=presentation.done
            ))
    
    return IdeaDetail(
        id=idea.id,
        title=idea.title,
        description=idea.description,
        status=idea.status,
        owners=owners,
        teamMembers=team_members,
        presentations=presentations,
        applicationId=idea.applicationId
    )

