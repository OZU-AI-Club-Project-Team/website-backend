import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException, status

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "a746b717be9fab1fa6ed250c50fb4eff788ac10b641755900166ddc1c707b2fc")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    data: JWT içine koyulacak payload
    expires_delta: token ne kadar süre geçerli olacak (varsayılan: ACCESS_TOKEN_EXPIRE_MINUTES).
    """
    to_encode = data.copy()

    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})

    # Token üretimi
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )





