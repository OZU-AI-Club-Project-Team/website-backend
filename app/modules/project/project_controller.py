from fastapi import HTTPException, status
from app.db import db
from app.modules.project.project_schema import (
    ProjectListItem,
    ProjectDetail,
    UserBasic,
    ProjectMemberDetail,
)
from typing import List, Optional


async def get_project_list(
    showcase: Optional[bool] = None,
    current_user_id: Optional[int] = None
) -> List[ProjectListItem]:
    """
    Get list of projects.
    If showcase is True, returns only showcase projects.
    If current_user_id is provided, calculates 'own' field.
    """
    # Build where clause
    where_clause = {"deletedAt": None}
    if showcase is True:
        where_clause["showcase"] = True
    
    projects = await db.project.find_many(
        where=where_clause,
        include={
            "leader": {
                "include": {
                    "teamMember": True
                }
            },
            "members": {
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
    for project in projects:
        # Determine if current user owns this project (is leader or member)
        own = False
        if current_user_id is not None:
            if project.leaderId == current_user_id:
                own = True
            else:
                # Check if user is a member
                for member in project.members:
                    if member.userId == current_user_id:
                        own = True
                        break
        
        result.append(ProjectListItem(
            id=project.id,
            title=project.title,
            date=project.createdAt,
            own=own,
            public=project.public,
            showcase=project.showcase
        ))
    
    return result


async def get_project_detail(
    project_id: int,
    current_user_id: Optional[int] = None
) -> ProjectDetail:
    """
    Get detailed information about a specific project.
    """
    project = await db.project.find_unique(
        where={"id": project_id},
        include={
            "leader": {
                "include": {
                    "teamMember": True
                }
            },
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
    )
    
    if project is None or project.deletedAt is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Build leader info
    leader = UserBasic(
        id=project.leader.id,
        email=project.leader.email,
        name=project.leader.name,
        surname=project.leader.surname,
        teamMember=project.leader.teamMember is not None
    )
    
    # Build members list
    members = []
    for member in project.members:
        members.append(ProjectMemberDetail(
            id=member.user.id,
            email=member.user.email,
            name=member.user.name,
            surname=member.user.surname,
            roles=member.roles,
            teamMember=member.user.teamMember is not None
        ))
    
    return ProjectDetail(
        id=project.id,
        title=project.title,
        description=project.description,
        status=project.status,
        public=project.public,
        showcase=project.showcase,
        date=project.createdAt,
        leader=leader,
        members=members,
        ideaId=project.ideaId
    )

