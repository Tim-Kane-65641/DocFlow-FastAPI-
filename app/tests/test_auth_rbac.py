import json
import base64
from fastapi.testclient import TestClient
from app.main import app
import pytest

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def user_token():
    return "eyJzdWIiOiAidV9kZW1vIiwgImVtYWlsIjogImRlbW9AZXhhbXBsZS5jb20iLCAicm9sZSI6ICJ1c2VyIn0="

@pytest.fixture
async def admin_token():
    return base64.b64encode(json.dumps({
        "sub": "admin1", "email": "admin@demo.com", "role": "admin"
    }).encode()).decode()

def test_jwt_isolation_and_role_enforcement(client, user_token, admin_token):
    # create doc as normal user
    files = {"file": ("priv.txt", b"private content", "text/plain")}
    data = {"primaryTag": "letters"}
    res = client.post("/v1/docs", data=data, files=files,
                      headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 200
    doc_id = res.json()["_id"]

    # another user cannot see it
    other_token = base64.b64encode(json.dumps({
        "sub": "other_user", "email": "x@demo.com", "role": "user"
    }).encode()).decode()
    res = client.get("/v1/folders/letters/docs",
                     headers={"Authorization": f"Bearer {other_token}"})
    assert res.status_code == 200
    assert all(d["_id"] != doc_id for d in res.json())

    # admin can see all docs
    res = client.get("/v1/folders/letters/docs",
                     headers={"Authorization": f"Bearer {admin_token}"})
    assert any(d["_id"] == doc_id for d in res.json())