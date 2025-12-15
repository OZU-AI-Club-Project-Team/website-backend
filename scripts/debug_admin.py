import sys
from pathlib import Path
# Ensure project root is on sys.path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app
from app.modules.user.user_router import get_current_user

client = TestClient(app)

# Non-admin
app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=2, role='STUDENT')
res = client.get('/users/admin-only')
print('non-admin ->', res.status_code, res.text)
app.dependency_overrides.clear()

# Admin
app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, role='ADMIN')
res = client.get('/users/admin-only')
print('admin ->', res.status_code, res.text)
app.dependency_overrides.clear()
