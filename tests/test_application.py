from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app
from app import db as real_db

client = TestClient(app)


def test_mark_read_forbidden():
    current_user = SimpleNamespace(id=2, role="STUDENT")

    from app.utils.security import get_current_user

    app.dependency_overrides[get_current_user] = lambda: current_user

    res = client.patch("/application/5/mark-read")
    assert res.status_code == 403
    app.dependency_overrides.clear()


def test_mark_read_success(monkeypatch):
    current_user = SimpleNamespace(id=1, role="ADMIN")

    async def find_app(*args, **kwargs):
        return SimpleNamespace(id=5, isRead=False)

    async def update_app(*args, **kwargs):
        return SimpleNamespace(id=5, isRead=True)

    monkeypatch.setattr(real_db.db, "application", SimpleNamespace(find_unique=find_app, update=update_app), raising=False)

    from app.utils.security import get_current_user

    app.dependency_overrides[get_current_user] = lambda: current_user

    res = client.patch("/application/5/mark-read")
    assert res.status_code == 200
    assert res.json() == {"id": 5, "isRead": True}
    app.dependency_overrides.clear()
