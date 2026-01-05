import pytest

from app.models import OpenAISettings, User
from app.utils.auth import create_access_token


@pytest.mark.asyncio
async def test_require_admin_for_stats_and_user_not_found(client, db_session):
    # non-admin cannot access stats
    u = User(username="na", email="na@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    token = create_access_token({"sub": str(u.id)})
    resp = await client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403

    # admin user but missing target user -> 404
    admin = User(username="adm4", email="adm4@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    await db_session.commit()
    token_admin = create_access_token({"sub": str(admin.id)})

    resp2 = await client.get("/api/v1/admin/users/9999", headers={"Authorization": f"Bearer {token_admin}"})
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_list_users_pagination_and_openai_models_success_and_failure(monkeypatch, client, db_session):
    admin = User(username="adm5", email="adm5@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    # create some users
    for i in range(3):
        db_session.add(User(username=f"u{i}", email=f"u{i}@example.com", password_hash="x"))
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    resp = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    # openai models failure when no api key
    resp2 = await client.get("/api/v1/admin/openai-models", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 400

    # set API key and mock AsyncOpenAI client
    s = OpenAISettings(id=1, api_key="sk-test")
    db_session.add(s)
    await db_session.commit()
    await db_session.refresh(s)

    class DummyModel:
        def __init__(self, id):
            self.id = id
            self.owned_by = "o"
            self.created = 123

    class DummyModelsResp:
        def __init__(self, data):
            self.data = data

    class DummyClient:
        def __init__(self, api_key=None):
            self.api_key = api_key

        class Models:
            @staticmethod
            async def list():
                return DummyModelsResp([DummyModel("gpt-4-test"), DummyModel("gpt-3.5-test")])

        @property
        def models(self):
            return self.Models

    # monkeypatch the import used inside the endpoint
    monkeypatch.setattr("openai.AsyncOpenAI", DummyClient, raising=False)

    resp3 = await client.get("/api/v1/admin/openai-models", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 200
    assert "models" in resp3.json()
