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
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

from app.modules.auth.auth_schema import (
    SendCodeRequest,
    SignInRequest,
    TokenResponse,
    #RefreshRequest,
)

CODE_TTL_MINUTES = 3


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _generate_code() -> str:
    # email için 6 haneli kod üret
    return f"{random.randint(0, 999999):06d}"


def _hash_code(code: str) -> str:
    # kodu hashle
    return hashlib.sha256(code.encode()).hexdigest()


# ========== PUBLIC CONTROLLER FONKSİYONLARI ==========

async def send_code(payload: SendCodeRequest) -> dict:
    await _send_verification_code_impl(payload.email)
    return {"message": "A verification code has been sent to your email address."}


async def signin(payload: SignInRequest, response: Response) -> TokenResponse:
    tokens = await _signin_user_impl(payload.email, payload.code)

    if tokens is None:
        # Eski router'da yaptığımız kontrolü artık burada yapıyoruz
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired code.",
        )

    access_token, refresh_token = tokens
    
    # Refresh tokeni HttpOnly cookie olarak ayarla
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # HTTPS kullanınca True yapılacak
        samesite="lax",  
        max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
        path="/auth/refresh",  # sadece /auth/refresh isteklerinde gönderilsin
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token= refresh_token,
    )


async def refresh(request: Request, response: Response) -> TokenResponse:
    
    #refresh tokeni cookieden çek
    refresh_token_cookie = request.cookies.get("refresh_token")
    if not refresh_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cookie not found",
        )
    
    tokens = await _refresh_tokens_impl(refresh_token_cookie)

    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    new_access_token, new_refresh_token = tokens

    # new_refresh_token i yeniden cookie olarak gönder (rotation)
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,  # PROD'da True
        samesite="lax",
        max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
        path="/auth/refresh",
    )


    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


# ========== PRIVATE İÇ İŞLEVLER (eski service'in gövdesi) ==========

async def _send_verification_code_impl(email: str) -> None:
    # 6 haneli kodu üret ve hashle
    raw_code = _generate_code()
    hashed = _hash_code(raw_code)

    expiry = _now_utc() + timedelta(minutes=CODE_TTL_MINUTES)

    # Aynı email için kullanılmamış eski kodları "used=True" yap
    await db.code.update_many(
        where={
            "email": email,
            "used": False,
        },
        data={
            "used": True,
        },
    )

    # Aynı email ve type için eski kodları sil
    await db.code.delete_many(
        where={
            "email": email,
            "type": CodeType.VERIFICATION,
        }
    )

    # Yeni kodu kaydet
    await db.code.create(
        data={
            "email": email,
            "hashedCode": hashed,
            "type": CodeType.VERIFICATION,
            "expiry": expiry,
        }
    )
    # GERÇEK MAIL ENTEGRASYONU İÇİN YER

    # Debug için konsol
    print(f"[DEBUG] Verification code for {email}: {raw_code} (expires at {expiry})")


async def _signin_user_impl(email: str, code: str) -> tuple[str, str] | None:
    # Kod kaydını bul
    record = await db.code.find_first(
        where={
            "email": email,
            "type": CodeType.VERIFICATION,
            "used": False,  # kullanılmamış olsun
        },
        order={
            "createdAt": "desc",
        },
    )

    if record is None:
        return None

    # Süresi dolmuş mu?
    if record.expiry < _now_utc():
        try:
            await db.code.update(
                where={"id": record.id},
                data={"used": True},
            )
        except RecordNotFoundError:
            pass
        return None

    # Kod yanlışsa attempts + used ayarla
    if record.hashedCode != _hash_code(code):
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
        return None

    # Kod doğru ise tamamen sil
    try:
        await db.code.delete(
            where={"id": record.id}
        )
    except RecordNotFoundError:
        pass

    # email'i eşleşen kullanıcıyı bul / oluştur
    user = await db.user.find_unique(
        where={"email": email},
    )

    if user is None:
        user = await db.user.create(
            data={
                "email": email,
                "key": secrets.token_hex(32),
                # "role": "STUDENT"  # default zaten
            }
        )

    # ACCESS TOKEN
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires,
    )

    # REFRESH TOKEN
    refresh_token = secrets.token_hex(64)
    refresh_expires_at = _now_utc() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    await db.refreshtoken.create(
        data={
            "token": refresh_token,
            "userId": user.id,
            "expiresAt": refresh_expires_at,
        }
    )

    return access_token, refresh_token


async def _refresh_tokens_impl(old_refresh_token: str) -> tuple[str, str] | None:
    now = _now_utc()

    # 1. Refresh token kaydını bul
    token_record = await db.refreshtoken.find_unique(
        where={"token": old_refresh_token},
        include={"user": True},
    )

    if (
        token_record is None
        or token_record.revoked
        or token_record.expiresAt < now
    ):
        return None

    user = token_record.user

    # 2. Eski refresh token'i iptal et
    await db.refreshtoken.update(
        where={"id": token_record.id},
        data={"revoked": True},
    )

    # 3. Yeni access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires,
    )

    # 4. Yeni refresh token oluştur
    new_refresh_token = secrets.token_hex(64)
    refresh_expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    await db.refreshtoken.create(
        data={
            "token": new_refresh_token,
            "userId": user.id,
            "expiresAt": refresh_expires_at,
        }
    )

    return new_access_token, new_refresh_token
