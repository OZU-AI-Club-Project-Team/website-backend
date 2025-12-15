from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app
from app import db as real_db

client = TestClient(app)


def test_get_user_found(monkeypatch):
    async def find_user(*args, **kwargs):
        return SimpleNamespace(
            id=5,
            email="u@example.com",
            name="U",
            surname="X",
            studentNumber="123",
            role="STUDENT",
            key="abc",
        )

    monkeypatch.setattr(real_db.db, "user", SimpleNamespace(find_unique=find_user))

    res = client.get("/users/5")
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "u@example.com"


def test_get_user_not_found(monkeypatch):
    async def find_user(*args, **kwargs):
        return None

    monkeypatch.setattr(real_db.db, "user", SimpleNamespace(find_unique=find_user))

    res = client.get("/users/999")
    assert res.status_code == 404


def test_get_team_member_profile(monkeypatch):
    async def find_tm(*args, **kwargs):
        return SimpleNamespace(
            id=5,
            workAreas=["BACKEND"],
            photoURL=None,
            bio="bio",
            github=None,
            linkedin=None,
            extraLinks=[],
            applicationId=None,
        )

    monkeypatch.setattr(
        real_db.db, "teammember", SimpleNamespace(find_unique=find_tm), raising=False
    )

    res = client.get("/users/5/team-member")
    assert res.status_code == 200
    data = res.json()
    assert data["bio"] == "bio"


def test_patch_user_forbidden(monkeypatch):
    # current user id different and not admin
    current_user = SimpleNamespace(id=2, role="STUDENT")

    async def find_user(*args, **kwargs):
        return SimpleNamespace(
            id=3, email="u@example.com", name="U", surname="X", studentNumber="123"
        )

    monkeypatch.setattr(real_db.db, "user", SimpleNamespace(find_unique=find_user))
    # override dependency via FastAPI dependency_overrides
    from app.modules.user.user_router import get_current_user

    app.dependency_overrides[get_current_user] = lambda: current_user

    res = client.patch("/users/3", json={"name": "New"})
    assert res.status_code == 403
    app.dependency_overrides.clear()


def test_patch_user_success(monkeypatch):
    current_user = SimpleNamespace(id=3, role="STUDENT")

    async def update_user(*args, **kwargs):
        return {
            "id": 3,
            "email": "u@example.com",
            "name": "New",
            "surname": "X",
            "studentNumber": "123",
            "role": "STUDENT",
            "key": "abc",
        }

    monkeypatch.setattr("app.modules.user.user_controller.update_user", update_user)
    from app.modules.user.user_router import get_current_user

    app.dependency_overrides[get_current_user] = lambda: current_user

    res = client.patch("/users/3", json={"name": "New"})
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 3
    assert data["email"] == "u@example.com"
    app.dependency_overrides.clear()
