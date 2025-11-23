from fastapi import APIRouter, Depends

from app.core.deps import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.get("/me")
async def get_me(current_user = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
    }

