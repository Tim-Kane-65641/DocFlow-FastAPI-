import json
import base64
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture(scope="session")
def user_token():
    return "eyJzdWIiOiAidV9kZW1vIiwgImVtYWlsIjogImRlbW9AZXBsZS5jb20iLCAicm9sZSI6ICJ1c2VyIn0="

@pytest.fixture(scope="session")
def admin_token():
    token = base64.b64encode(json.dumps({
        "sub": "admin1", "email": "admin@demo.com", "role": "admin"
    }).encode()).decode()
    return token

def test_credits_tracking_on_scoped_actions(client, user_token):
    payload = {
        "scope": {"type": "folder", "name": "invoices"},
        "messages": [{"role": "user", "content": "make csv"}],
        "actions": ["make_csv"]
    }

    res = client.post(
        "/v1/actions/run",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["credits_charged"] == 5

    res = client.get(
        "/v1/actions/usage/month",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert res.status_code == 200
    usage = res.json()
    assert usage["credits"] >= 5
