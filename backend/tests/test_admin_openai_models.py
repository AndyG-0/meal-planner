import pytest
from app.models import User, OpenAISettings
from app.utils.auth import create_access_token


class DummyModel:
    def __init__(self, id):
        self.id = id
        self.owned_by = "openai"
        self.created = 0


class DummyModelsResponse:
    def __init__(self, data):
        self.data = data


class DummyClient:
    def __init__(self, api_key=None):
        self.models = self
        self.api_key = api_key

    async def list(self):
        # Return a mixture of models including excluded patterns
        data = [DummyModel("gpt-4o-mini"), DummyModel("gpt-3.5-turbo"), DummyModel("whisper-1"), DummyModel("davinci-002")]
        return DummyModelsResponse(data)


@pytest.mark.asyncio
async def test_get_openai_models_requires_key(client, db_session, test_user):
    admin = User(username="oadm", email="oadm@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    # Ensure no OpenAI settings exist
    resp = await client.get("/api/v1/admin/openai-models", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_openai_models_success(monkeypatch, client, db_session, test_user):
    admin = User(username="oadm2", email="oadm2@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)

    # create settings with api key
    s = OpenAISettings(id=1, api_key="sk-test")
    db_session.add(s)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    # monkeypatch openai.AsyncOpenAI to our DummyClient
    import openai

    monkeypatch.setattr(openai, "AsyncOpenAI", lambda api_key=None: DummyClient(api_key=api_key))

    resp = await client.get("/api/v1/admin/openai-models", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    # Ensure that excluded models (like whisper/davinci) are not included
    assert all(not ("whisper" in m["id"] or "davinci" in m["id"]) for m in data["models"])