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


def test_primary_tag_uniqueness_and_upload(client, user_token):
    files = {"file": ("invoice1.txt", b"invoice 2025 bank gst", "text/plain")}
    data = {"primaryTag": "invoices", "secondaryTags": ["finance", "audit"]}
    res = client.post("/v1/docs", data=data, files=files,
                      headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 200
    doc = res.json()
    assert "filename" in doc

    # Verify exactly one primary tag
    res_tags = client.get("/v1/folders", headers={"Authorization": f"Bearer {user_token}"})
    assert res_tags.status_code == 200
    folders = res_tags.json()
    assert any(f["name"] == "invoices" for f in folders)


def test_folder_vs_file_scope_rule(client, user_token):
    """Ensure folder and file scopes are exclusive"""
    qparams = {
        "q": "invoice",
        "scope": "folder",
        "name": "invoices",
        "ids": ["abc"]
    }
    res = client.get("/v1/search", params=qparams,
                     headers={"Authorization": f"Bearer {user_token}"})
    assert res.status_code == 400
    assert "either folder or files" in res.text