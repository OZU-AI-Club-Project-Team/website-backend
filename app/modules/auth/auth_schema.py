from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.modules.user.user_schema import UserRole

class SendCodeRequest(BaseModel):
    email: EmailStr
    
class SendCodeResponse(BaseModel):
    resend: bool
    expiry: datetime

class SignInRequest(BaseModel):
    email: EmailStr
    code: str

class SignInResponse(BaseModel):
    role: UserRole
    #accessToken: str   --> artık cookie ile taşınıyor

class RefreshResponse(BaseModel):
    ok: bool

class ResetKeyRequest(BaseModel):
    email: EmailStr
    code: str

class ResetKeyResponse(BaseModel):
    ok: bool