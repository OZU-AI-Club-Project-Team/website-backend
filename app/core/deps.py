from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import verify_access_token
from app.db import db

#Urlsinden tokeni aldık
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    #1.token'den user_id'yi çıkar
    user_id = verify_access_token(token)

    #2.DB'de kullanıcı var mı kontrol et
    user = await db.user.find_unique(
        where={"id": int(user_id)}
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


