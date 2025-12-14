from fastapi import APIRouter, Request, Response


from app.modules.auth.auth_schema import (
    SendCodeRequest,
    SendCodeResponse,
    SignInRequest,
    SignInResponse,
    #RefreshRequest,
    RefreshResponse,
    ResetKeyRequest,
    ResetKeyResponse,
)

from app.modules.auth import auth_controller


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/send-code", response_model=SendCodeResponse)
async def send_code(payload: SendCodeRequest):
    return await auth_controller.send_code(payload)


@router.post("/signin", response_model=SignInResponse)
async def signin(payload: SignInRequest, response: Response):
    return await auth_controller.signin(payload, response)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(request: Request, response: Response):
    return await auth_controller.refresh(request, Response)

@router.post("/reset-key", response_model=ResetKeyResponse)
async def reset_key(payload: ResetKeyRequest, request: Request, response: Response):
    return await auth_controller.reset_key(payload, request, response)



