from datetime import datetime, timedelta, timezone
import secrets
import hashlib
import random

from fastapi import HTTPException, status, Request, Response

from prisma.errors import RecordNotFoundError
from prisma.enums import CodeType

from app.db import db
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

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
from app.modules.user.user_schema import UserRole

CODE_TTL_MINUTES = 3
ACCESS_COOKIE_NAME = "access_token"
SESSION_COOKIE_NAME = "session_id"


# ~~HELPERS~~ gerekirse utilse koyulabilir

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _generate_code() -> str:
    # email için 6 haneli kod üret
    return f"{random.randint(0, 999999):06d}"


def _hash_code(code: str) -> str:
    # kodu hashle
    return hashlib.sha256(code.encode()).hexdigest()

def _set_access_cookie(response: Response, token: str) -> None:
    response.set.cookie(
        key=ACCESS_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=int(ACCESS_TOKEN_EXPIRE_MINUTES) * 60,
        path="/",
    )

def _set_session_cookie(response: Respose, session_id: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=int(REFRESH_TOKEN_EXPIRE_DAYS)*24*60*60,
        path="/",
    )

def _clear_cookie(response: Response, name: str) -> None:
    response.delete_cookie(key=name, path="/")

def _new_session_id() -> str:
    return secrets.token_urlsafe(48)




# ========== PUBLIC CONTROLLER FONKSİYONLARI ==========

async def send_code(payload: SendCodeRequest) -> SendCodeResponse:
    # 6 haneli kodu üret ve hashle
    raw_code = _generate_code()
    hashed = _hash_code(raw_code)

    expiry = _now_utc() + timedelta(minutes=CODE_TTL_MINUTES)

    existing_code = await db.code.find_first(
        where={
            "email": payload.email,
            "used": False,
            "type": CodeType.VERIFICATION,
            "expiry": {"gt": _now_utc()}
        }
    )

    resend = existing_code is not None


    # Aynı email için kullanılmamış eski kodları "used=True" yap
    await db.code.update_many(
        where={
            "email": payload.email,
            "used": False,
        },
        data={
            "used": True,
        },
    )

    # Aynı email ve type için kullanılmış eski kodları sil
    await db.code.delete_many(
        where={
            "email": payload.email,
            "used": True,
            "type": CodeType.VERIFICATION,
        }
    )

    # Yeni kodu oluştur ve kaydet
    await db.code.create(
        data={
            "email": payload.email,
            "hashedCode": hashed,
            "type": CodeType.VERIFICATION,
            "expiry": expiry,
        }
    )

    # GERÇEK MAIL ENTEGRASYONU İÇİN YER



    # Debug için konsol
    print(f"[DEBUG] Verification code for {payload.email}: {raw_code} (expires at {expiry})")
    
    return SendCodeResponse(resend=resend, expiry=expiry)


async def signin(payload: SignInRequest, response: Response) -> SignInResponse:
    
    # Kod kaydını bul
    record = await db.code.find_first(
        where={
            "email": payload.email,
            "hashedCode": payload.code,
            "used": False,
            "type": CodeType.VERIFICATION,
        },
        order={
            "createdAt": "desc",
        },
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired code",
        )

    # Süresi dolmuş mu?
    if record.expiry < _now_utc():
        try:
            #dolmamışsa
            await db.code.update(
                where={"id": record.id},
                data={"used": True},
            )
        except RecordNotFoundError:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired code",
        )

    # Kod yanlışsa attempts + used ayarla
    if record.hashedCode != _hash_code(payload.code):
        try:
            await db.code.update(
                where={"id": record.id},
                data={
                    "used": True,
                    "attempts": record.attempts + 1,
                },
            )
        except RecordNotFoundError:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired code",
        )
    else:
        # Kod doğru ise tamamen sil
        try:
            await db.code.delete(
                where={"id": record.id}
            )
        except RecordNotFoundError:
            pass

    # email'i eşleşen kullanıcıyı bul / oluştur
    user = await db.user.find_unique(where={"email": payload.email},)

    if user is None:
        user = await db.user.create(
            data={
                "email": payload.email,
                "key": secrets.token_hex(32),
                # "role": "STUDENT"  # default zaten
            }
        )

    # ACCESS TOKEN
    access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )

    # REFRESH TOKEN
    session_id = _new_session_id()
    session_expires_at = _now_utc + timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS))

    await db.refreshtoken.create(
        data={
            "token": session_id,
            "userId": user.id,
            "expiresAt": session_expires_at,
        }
    )

    return SignInResponse(role=user.role)


async def refresh(request: Request, response: Response) -> RefreshResponse:
    #session_id --> refresh token
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session cookie not found",
        )
    
    token_record = await db.refreshtoken.find_unique(
        where={"token": session_id},
        include={"user": True},
    )

    if (
        token_record is None
        or token_record.revoked
        or token_record.expiresAt < _now_utc
        or token_record.user is None
    ):
        _clear_cookie(response, ACCESS_COOKIE_NAME)
        _clear_cookie(response, SESSION_COOKIE_NAME)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
    
    #db'deki refresh token'in içindeki user'ı al
    user = token_record.user

    await db.refreshtoken.update(
        where={"id": token_record.id},
        data={"revoked": True},
    )

    _new_session_id = _new_session_id()
    new_session_expires_at = _now_utc() + timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS))

    await db.refreshtoken.create(
        data={
            "token": _new_session_id,
            "userId": user.id,
            "expiresAt": new_session_expires_at,
        }
    )
    new_access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    _set_access_cookie(response, new_access_token)
    _set_session_cookie(response, _new_session_id)

    return RefreshResponse(ok=True)                                                


async def reset_key(payload: ResetKeyRequest, response: Response) -> ResetKeyResponse:
    
    record = await db.code.find_first(
        where={
            "email": payload.email,
            "hashedCode": payload.code,
            "used": False,
            "type": CodeType.RESET_KEY,
            "expiry": {"gt": _now_utc()},
        },
        order={"createdAt": "desc"},
    )

    if record is None or record.expiry < _now_utc() or record.hashedCode != _hash_code(payload.code):
        if record is not None:
            try:
                await db.code.update(where={"id": record.id}, data={"used": True})
            except RecordNotFoundError:
                pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired code",
        )
    
    try:
        await db.code.delete(where={"id": record.id})
    except RecordNotFoundError:
        pass

    user = await db.user.find_unique(where={"email": payload.email})

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    new_key = create_refresh_token({"sub": str(user.id)})

    await db.user.update(
        where={"id": user.id},
        data={"key": new_key},
    )

    await db.refreshtoken.update_many(
        where={"userId": user.id, "revoked": False},
        data={"revoked": True},
    )

    session_id = _new_session_id()
    session_expires_at = _now_utc() + timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS))

    await db.refreshtoken.create(
        data={
            "token": session_id,
            "userId": user.id,
            "expiresAt": session_expires_at,
        }
    )

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    _set_access_cookie(response, access_token)
    _set_session_cookie(response, session_id)

    return ResetKeyResponse(ok=True)

