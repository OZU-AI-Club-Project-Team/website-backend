from fastapi import HTTPException, status

from app.db import db


async def get_user(user_id: int):
    user = await db.user.find_unique(where={"id": user_id})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return {
        "id": user.id,
        "email": user.email,
        "role": getattr(user, "role", None),
        "key": getattr(user, "key", None),
        "name": getattr(user, "name", None),
        "surname": getattr(user, "surname", None),
        "studentNumber": getattr(user, "studentNumber", None),
        "teamMember": getattr(user, "teamMember", None) is not None,
    }


async def get_team_member_profile(user_id: int):
    tm = await db.teammember.find_unique(where={"id": user_id})
    if tm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member profile not found",
        )
    return {
        "id": tm.id,
        "workAreas": tm.workAreas,
        "photoURL": tm.photoURL,
        "bio": tm.bio,
        "github": tm.github,
        "linkedin": tm.linkedin,
        "extraLinks": tm.extraLinks,
        "applicationId": tm.applicationId,
    }


async def update_user(user_id: int, data: dict, current_user) -> dict:
    await db.user.update(where={"id": user_id}, data=data)
    updated = await db.user.find_unique(where={"id": user_id})
    return {
        "id": updated.id,
        "email": updated.email,
        "role": getattr(updated, "role", None),
        "key": getattr(updated, "key", None),
        "name": updated.name,
        "surname": updated.surname,
        "studentNumber": updated.studentNumber,
    }
