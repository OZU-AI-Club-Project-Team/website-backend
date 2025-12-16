from fastapi import APIRouter, Depends

from app.utils.security import get_current_user, require_admin_or_self  # noqa: F401 (exported for tests)
from fastapi import Path, Body

from app.modules.user import user_controller
from app.modules.user.user_schema import User

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


# Admin-only static route should be defined before dynamic `/{id}` routes
#@router.get("/admin-only")
#async def admin_only(current_user=Depends(require_roles("ADMIN"))):
#        """Example admin-only endpoint for testing role-based dependency."""
#    return {"ok": True}


@router.get("/{id}", response_model=User)
async def get_user(id: int = Path(..., ge=1)):
    return await user_controller.get_user(id)


@router.get("/{id}/team-member")
async def get_team_member(id: int = Path(..., ge=1)):
    return await user_controller.get_team_member_profile(id)


@router.patch("/{id}", response_model=User)
async def patch_user(id: int, payload: dict = Body(...), current_user=Depends(require_admin_or_self)):
    return await user_controller.update_user(id, payload, current_user)


