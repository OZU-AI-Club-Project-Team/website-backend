from fastapi import APIRouter, Request, Response

from app.modules.auth.auth_schema import (
    SendCodeRequest,
    SignInRequest,
    #RefreshRequest,
    TokenResponse,
)
from app.modules.auth import auth_controller

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/send-code")
async def send_code(payload: SendCodeRequest):
    return await auth_controller.send_code(payload)


@router.post("/signin", response_model=TokenResponse)
async def signin(payload: SignInRequest, response: Response):
    return await auth_controller.signin(payload, response)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response): # Normalde payload: RefreshRequest yazıyordu
    return await auth_controller.refresh(request, response) # payload yerine
