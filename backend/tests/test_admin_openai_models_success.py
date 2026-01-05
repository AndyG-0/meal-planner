import pytest
from app.utils.auth import create_access_token


@pytest.mark.asyncio
async def test_openai_models_success(client, db_session, monkeypatch):
    from app.models import User, OpenAISettings

    admin = User(username="modelsadmin", email="ma2@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    # Set API key so endpoint proceeds to call OpenAI
    settings = OpenAISettings(id=1, api_key="sk-test")
    db_session.add(settings)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

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
                return FakeModelsResp([
                    FakeModel("gpt-4o", "openai", 1),
                    FakeModel("gpt-3.5-turbo", "openai", 2),
                    FakeModel("whisper-1", "openai", 3),
                ])

    monkeypatch.setattr("openai.AsyncOpenAI", FakeAsyncOpenAI)

    resp = await client.get("/api/v1/admin/openai-models", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    models = resp.json()["models"]
    ids = [m["id"] for m in models]
    assert any("gpt-4o" in i for i in ids)
    assert any("gpt-3.5" in i for i in ids)
    assert not any("whisper" in i for i in ids)
