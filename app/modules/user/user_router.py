from fastapi import APIRouter, Depends

from app.utils.security import get_current_user
from fastapi import Path, Body

from app.modules.user import user_controller
from app.modules.user.user_schema import User

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
    }


@router.get("/{id}", response_model=User)
async def get_user(id: int = Path(..., ge=1)):
    return await user_controller.get_user(id)


@router.get("/{id}/team-member")
async def get_team_member(id: int = Path(..., ge=1)):
    return await user_controller.get_team_member_profile(id)


@router.patch("/{id}", response_model=User)
async def patch_user(
    id: int, payload: dict = Body(...), current_user=Depends(get_current_user)
):
    return await user_controller.update_user(id, payload, current_user)
