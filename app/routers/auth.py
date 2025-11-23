from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import SendCodeRequest, SignInRequest, TokenResponse, RefreshRequest
from app.services.auth_service import send_verification_code, signin_user, refresh_tokens

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/send-code")
async def send_code(payload: SendCodeRequest):
    await send_verification_code(payload.email)

    return {"message": "A verification code has been sent to your email address."}

@router.post("/signin", response_model=TokenResponse)
async def signin(payload: SignInRequest):
    tokens = await signin_user(payload.email, payload.code)
    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired code."
        )
    
    access_token, refresh_token = tokens
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest):
    tokens = await refresh_tokens(payload.refresh_token)
    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    access_token, refresh_token = tokens
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )
