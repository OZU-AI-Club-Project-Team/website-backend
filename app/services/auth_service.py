from datetime import datetime, timedelta, timezone
import secrets
import hashlib
import random

from app.db import db

from prisma.errors import RecordNotFoundError
from app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

CODE_TTL_MINUTES = 3

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def generate_code() -> str:
    # email için 6 haneli kod üret
    return f"{random.randint(0, 999999):06d}"

def hash_code(code: str) -> str:
    #kodu hashle
    return hashlib.sha256(code.encode()).hexdigest()

async def send_verification_code(email: str) -> None:

    #6 haneli kodu üret ve hashle
    raw_code = generate_code()
    hashed = hash_code(raw_code)

    expiry = _now_utc() + timedelta(minutes=CODE_TTL_MINUTES)

    #Kodu güncelle
    await db.code.update_many(
        where={
            "email": email,
            "used": False,
        },
        data={
            "used": True,
        },
    )

    #Aynı email ve type için eski kodları sil
    await db.code.delete_many(
        where={
            "email": email,
            "type": "VERIFICATION",
        }
    )

    #Yeni kodu kaydet
    await db.code.create(
        data={
            "email": email,
            "hashedCode": hashed,
            "type": "VERIFICATION",
            "expiry": expiry,
        }
    )
    #GERCEK KODU KAYDETME ENTEGRASYONU

    #debug için konsol
    print(f"[DEBUG] Verification code for {email}: {raw_code} (expires at {expiry})")



async def signin_user(email: str, code: str) -> str | None:
    # Kod kaydını bul
    record = await db.code.find_first(
        where={
            "email": email,
            "type": "VERIFICATION",
            "used": False, #kullanılmamış olsun
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

    # Kod geçerli, artık bir daha kullanılamasın:
    # Used özelliği belirliyor, konuştuğumuz gibi
    if record.hashedCode != hash_code(code):
        try:
            await db.code.update(
                where={"id": record.id},
                data={"used": True,
                      "attempts": record.attempts+1,
                },
            )
        except RecordNotFoundError:
            pass
        return None
    
    #Kod doğru ise bir daha kullanılmaması için sil
    try:
        await db.code.delete(
            where={"id": record.id}
        )
    except RecordNotFoundError:
        pass

    #emaili eşleşen kullanıcıyı bul ve oluştur
    user = await db.user.find_unique(
        where={"email": email},
    )

    if user is None:
        user = await db.user.create(
            data={
                "email": email,
                "key": secrets.token_hex(32),
                #"role": "STUDENT" #zaten default, gerek yok ama burda dursun
            }
        )

    #gpt email yerine id kullanmayı önerdi - sor
    # ACCESS TOKEN
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires,
    )
    
    #REFRESH TOKEN
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


async def refresh_tokens(old_refresh_token: str) -> tuple[str, str] | None:
    now = _now_utc()

    # 1.Refresh token kaydını bul
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

    # 2.Eski refresh token'i iptal et
    await db.refreshtoken.update(
        where={"id": token_record.id},
        data={"revoked": True},
    )

    # 3.Yeni access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires,
    )

    # 4.Yeni refresh token oluştur
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










