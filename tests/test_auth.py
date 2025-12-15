from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app import db as real_db
from app.modules.auth.auth_controller import _hash_code

client = TestClient(app)

# Helpers to create async stubs


def async_fn(return_value=None):
    async def _fn(*args, **kwargs):
        return return_value

    return _fn


def test_send_code_returns_expiry(monkeypatch):
    # Stub db.code methods
    monkeypatch.setattr(
        real_db.db,
        "code",
        SimpleNamespace(
            find_first=async_fn(None),
            update_many=async_fn(None),
            delete_many=async_fn(None),
            create=async_fn(None),
        ),
    )

    res = client.post("/auth/send-code", json={"email": "test@example.com"})
    assert res.status_code == 200
    data = res.json()
    assert "resend" in data and "expiry" in data


def test_signin_sets_cookies_and_returns_role(monkeypatch):
    code = "123456"
    hashed = _hash_code(code)
    future = datetime.now(timezone.utc) + timedelta(minutes=5)

    record = SimpleNamespace(id=1, hashedCode=hashed, expiry=future, attempts=0)

    async def find_first_code(*args, **kwargs):
        return record

    async def delete_code(*args, **kwargs):
        return None

    async def find_user(*args, **kwargs):
        return None

    async def create_user(*args, **kwargs):
        return SimpleNamespace(id=42, role="STUDENT", email="test@example.com")

    async def create_refreshtoken(*args, **kwargs):
        return None

    monkeypatch.setattr(
        real_db.db,
        "code",
        SimpleNamespace(find_first=find_first_code, delete=delete_code),
    )
    monkeypatch.setattr(
        real_db.db, "user", SimpleNamespace(find_unique=find_user, create=create_user)
    )
    monkeypatch.setattr(
        real_db.db, "refreshtoken", SimpleNamespace(create=create_refreshtoken)
    )

    res = client.post("/auth/signin", json={"email": "test@example.com", "code": code})
    assert res.status_code == 200
    data = res.json()
    assert data.get("role") == "STUDENT"

    # Cookies should be set
    cookies = res.cookies
    assert "access_token" in cookies
    assert "session_id" in cookies


def test_refresh_with_body_returns_access_token_and_sets_cookies(monkeypatch):
    now = datetime.now(timezone.utc)
    session = "session-abc"
    user = SimpleNamespace(id=42, role="STUDENT", email="test@example.com")
    token_record = SimpleNamespace(
        id=1, token=session, revoked=False, expiresAt=now + timedelta(days=1), user=user
    )

    async def find_token(*args, **kwargs):
        return token_record

    async def update_token(*args, **kwargs):
        return None

    async def create_token(*args, **kwargs):
        return None

    monkeypatch.setattr(
        real_db.db,
        "refreshtoken",
        SimpleNamespace(
            find_unique=find_token, update=update_token, create=create_token
        ),
    )

    res = client.post("/auth/refresh", json={"refreshToken": session})
    assert res.status_code == 200
    data = res.json()
    assert "accessToken" in data
    # cookies should be set for browser clients
    assert "access_token" in res.cookies
    assert "session_id" in res.cookies


def test_refresh_with_cookie_returns_access_token(monkeypatch):
    now = datetime.now(timezone.utc)
    session = "session-cookie"
    user = SimpleNamespace(id=42, role="STUDENT", email="test@example.com")
    token_record = SimpleNamespace(
        id=1, token=session, revoked=False, expiresAt=now + timedelta(days=1), user=user
    )

    async def find_token(*args, **kwargs):
        return token_record

    async def update_token(*args, **kwargs):
        return None

    async def create_token(*args, **kwargs):
        return None

    monkeypatch.setattr(
        real_db.db,
        "refreshtoken",
        SimpleNamespace(
            find_unique=find_token, update=update_token, create=create_token
        ),
    )

    client.cookies.set("session_id", session)
    res = client.post("/auth/refresh")
    assert res.status_code == 200
    data = res.json()
    assert "accessToken" in data


def test_reset_key_success_sets_cookies_and_returns_ok(monkeypatch):
    now = datetime.now(timezone.utc)
    code = "654321"
    hashed = _hash_code(code)

    record = SimpleNamespace(id=1, hashedCode=hashed, expiry=now + timedelta(minutes=5))
    user = SimpleNamespace(id=99, email="reset@example.com")

    async def find_code(*args, **kwargs):
        return record

    async def delete_code(*args, **kwargs):
        return None

    async def find_user(*args, **kwargs):
        return user

    async def update_user(*args, **kwargs):
        return None

    async def update_many_rt(*args, **kwargs):
        return None

    async def create_rt(*args, **kwargs):
        return None

    monkeypatch.setattr(
        real_db.db, "code", SimpleNamespace(find_first=find_code, delete=delete_code)
    )
    monkeypatch.setattr(
        real_db.db, "user", SimpleNamespace(find_unique=find_user, update=update_user)
    )
    monkeypatch.setattr(
        real_db.db,
        "refreshtoken",
        SimpleNamespace(update_many=update_many_rt, create=create_rt),
    )

    res = client.post(
        "/auth/reset-key", json={"email": "reset@example.com", "code": code}
    )
    assert res.status_code == 200
    data = res.json()
    assert data.get("ok") is True
    assert "access_token" in res.cookies
    assert "session_id" in res.cookies


def test_reset_key_user_not_found_returns_404(monkeypatch):
    now = datetime.now(timezone.utc)
    code = "000000"
    hashed = _hash_code(code)

    record = SimpleNamespace(id=2, hashedCode=hashed, expiry=now + timedelta(minutes=5))

    async def find_code(*args, **kwargs):
        return record

    async def delete_code(*args, **kwargs):
        return None

    async def find_user(*args, **kwargs):
        return None

    monkeypatch.setattr(
        real_db.db, "code", SimpleNamespace(find_first=find_code, delete=delete_code)
    )
    monkeypatch.setattr(real_db.db, "user", SimpleNamespace(find_unique=find_user))

    res = client.post(
        "/auth/reset-key", json={"email": "nope@example.com", "code": code}
    )
    assert res.status_code == 401 or res.status_code == 404
