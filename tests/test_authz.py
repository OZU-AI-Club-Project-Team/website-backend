from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_admin_only_forbidden():
    # non-admin user should be forbidden
    current_user = SimpleNamespace(id=2, role="STUDENT")

    from app.modules.user.user_router import get_current_user

    app.dependency_overrides[get_current_user] = lambda: current_user

    res = client.get("/users/admin-only")
    assert res.status_code == 403
    app.dependency_overrides.clear()


def test_admin_only_success():
    # admin user should succeed
    current_user = SimpleNamespace(id=1, role="ADMIN")

    from app.modules.user.user_router import get_current_user

    app.dependency_overrides[get_current_user] = lambda: current_user

    res = client.get("/users/admin-only")
    assert res.status_code == 200
    assert res.json() == {"ok": True}
    app.dependency_overrides.clear()
