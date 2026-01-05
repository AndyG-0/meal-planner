import pytest
from app.models import User, OpenAISettings
from app.utils.auth import create_access_token


class BadClient:
    def __init__(self, api_key=None):
        pass

    async def list(self):
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_get_openai_models_handles_client_error(monkeypatch, client, db_session, test_user):
    admin = User(username="badadm", email="badadm@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    s = OpenAISettings(id=1, api_key="sk-test")
    db_session.add(s)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    import openai
    monkeypatch.setattr(openai, "AsyncOpenAI", lambda api_key=None: BadClient())

    resp = await client.get("/api/v1/admin/openai-models", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
    assert "Failed to retrieve OpenAI models" in resp.json()["detail"]
