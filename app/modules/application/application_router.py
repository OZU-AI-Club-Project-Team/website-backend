from fastapi import APIRouter, Path, Depends
from app.utils.security import require_roles
from app.modules.application import application_controller

router = APIRouter(prefix="/application", tags=["application"])


@router.patch("/{id}/mark-read")
async def mark_read(id: int = Path(..., ge=1), current_user=Depends(require_roles("ADMIN"))):
    return await application_controller.mark_read(id)
