
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


def test_webhook_classification_and_rate_limit(client, user_token):
    ad_payload = {
        "source": "scanner-01",
        "imageId": "img_123",
        "text": "LIMITED TIME SALE unsubscribe: mailto:stop@brand.com",
        "meta": {"address": "123 Main St"}
    }
    official_payload = {
        "source": "scanner-01",
        "imageId": "img_999",
        "text": "Court notice regarding bank statement and GST filing",
        "meta": {}
    }

    # ad → classified + task created
    res = client.post("/v1/webhooks/ocr", json=ad_payload,
                      headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 200
    j = res.json()
    assert j["classification"] == "ad"
    assert j["task_created"] is True

    # official → classified
    res = client.post("/v1/webhooks/ocr", json=official_payload,
                      headers={"Authorization": f"Bearer {user_token}"})
    assert res.json()["classification"] == "official"

    # simulate rate limit
    for _ in range(3):
        client.post("/v1/webhooks/ocr", json=ad_payload,
                    headers={"Authorization": f"Bearer {user_token}"})
    r = client.post("/v1/webhooks/ocr", json=ad_payload,
                    headers={"Authorization": f"Bearer {user_token}"})
    assert r.json()["task_created"] is False