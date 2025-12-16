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
