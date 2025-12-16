from fastapi import APIRouter, Path, Query, Depends, Security, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.modules.project import project_controller
from app.modules.project.project_schema import (
    ProjectListItem,
    ProjectDetail,
)
from app.utils.security import verify_access_token
from app.db import db
from typing import List, Optional

router = APIRouter(prefix="/project", tags=["project"])

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


@router.get("", response_model=List[ProjectListItem])
async def get_project_list(
    showcase: Optional[bool] = Query(None, description="If true, returns only showcase projects"),
    current_user_id: Optional[int] = Depends(get_optional_current_user_id)
):
    """
    Get list of projects.
    If showcase is True, returns only showcase projects.
    """
    return await project_controller.get_project_list(
        showcase=showcase,
        current_user_id=current_user_id
    )


@router.get("/{id}", response_model=ProjectDetail)
async def get_project_detail(
    id: int = Path(..., ge=1),
    current_user_id: Optional[int] = Depends(get_optional_current_user_id)
):
    """
    Get detailed information about a specific project.
    """
    return await project_controller.get_project_detail(
        project_id=id,
        current_user_id=current_user_id
    )

