from fastapi import APIRouter, Path, Depends, Security, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.modules.idea import idea_controller
from app.modules.idea.idea_schema import (
    IdeaListItem,
    IdeaDetail,
)
from app.utils.security import verify_access_token
from app.db import db
from typing import List, Optional

router = APIRouter(prefix="/idea", tags=["idea"])

# Create optional OAuth2 scheme (doesn't raise error if token missing)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/signin", auto_error=False)


async def get_optional_current_user_id(
    token: Optional[str] = Security(oauth2_scheme_optional)
) -> Optional[int]:
    """
    Optional dependency to get current user ID.
    Returns None if user is not authenticated.
    """
    if not token:
        return None
    
    try:
        user_id = verify_access_token(token)
        user = await db.user.find_unique(where={"id": int(user_id)})
        return user.id if user else None
    except (HTTPException, Exception):
        # If authentication fails, return None (public access)
        return None


@router.get("", response_model=List[IdeaListItem])
async def get_idea_list(
    current_user_id: Optional[int] = Depends(get_optional_current_user_id)
):
    """
    Get list of ideas.
    """
    return await idea_controller.get_idea_list(
        current_user_id=current_user_id
    )


@router.get("/{id}", response_model=IdeaDetail)
async def get_idea_detail(
    id: int = Path(..., ge=1),
    current_user_id: Optional[int] = Depends(get_optional_current_user_id)
):
    """
    Get detailed information about a specific idea.
    """
    return await idea_controller.get_idea_detail(
        idea_id=id,
        current_user_id=current_user_id
    )

