import pytest
from app.utils.auth import create_access_token


@pytest.mark.asyncio
async def test_feature_toggles_crud(client, db_session):
    # create admin
    from app.models import User

    admin = User(username="ftadmin", email="ft@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    # Create toggle
    resp = await client.post(
        "/api/v1/admin/feature-toggles",
        json={"feature_key": "test_feature", "feature_name": "Test Feature", "is_enabled": True, "description": "t1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    t = resp.json()
    assert t["feature_key"] == "test_feature"

    # List
    resp = await client.get("/api/v1/admin/feature-toggles", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(x["feature_key"] == "test_feature" for x in resp.json())

    # Get single
    resp = await client.get("/api/v1/admin/feature-toggles/test_feature", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # Patch
    resp = await client.patch("/api/v1/admin/feature-toggles/test_feature", json={"is_enabled": False}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["is_enabled"] is False

    # Delete
    resp = await client.delete("/api/v1/admin/feature-toggles/test_feature", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_openai_settings_and_models(client, db_session, monkeypatch):
    from app.models import User, OpenAISettings

    admin = User(username="openadmin", email="oa@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    await db_session.commit()
    token = create_access_token({"sub": str(admin.id)})

    # GET should create default if none exists
    resp = await client.get("/api/v1/admin/openai-settings", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "has_api_key" in data

    # PATCH to set a key and searxng_url
    resp = await client.patch(
        "/api/v1/admin/openai-settings",
        json={"api_key": "sk-test", "searxng_url": "http://searx"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_api_key"] is True
    assert data["searxng_url"] == "http://searx"

    # Now test models listing by monkeypatching AsyncOpenAI.models.list
    class FakeModel:
        def __init__(self, id, owned_by, created):
            self.id = id
            self.owned_by = owned_by
            self.created = created

    class FakeModelsResp:
        def __init__(self, data):
            self.data = data

    class FakeAsyncOpenAI:
        def __init__(self, api_key=None):
            self.api_key = api_key

        class models:
            @staticmethod
            async def list():
                return FakeModelsResp(
                    [
                        FakeModel("gpt-4o", "openai", 1),
                        FakeModel("whisper-1", "openai", 2),
                        FakeModel("gpt-3.5-turbo", "openai", 3),
                    ]
                )

    monkeypatch.setattr("openai.AsyncOpenAI", FakeAsyncOpenAI)

    resp = await client.get("/api/v1/admin/openai-models", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    models = resp.json()["models"]
    # Should include gpt-4o and gpt-3.5-turbo, but not whisper
    ids = [m["id"] for m in models]
    assert any("gpt-4o" in i for i in ids)
    assert any("gpt-3.5" in i for i in ids)
    assert not any("whisper" in i for i in ids)


@pytest.mark.asyncio
async def test_session_settings_get_and_patch(client, db_session):
    from app.models import User

    admin = User(username="sessadmin", email="sa@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    await db_session.commit()
    token = create_access_token({"sub": str(admin.id)})

    resp = await client.get("/api/v1/admin/session-settings", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "session_ttl_unit" in data

    resp = await client.patch("/api/v1/admin/session-settings", json={"session_ttl_value": 30, "session_ttl_unit": "minutes"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["session_ttl_value"] == 30
