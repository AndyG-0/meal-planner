import pytest

from app.utils.auth import create_access_token


@pytest.mark.asyncio
async def test_openai_models_error(client, db_session, monkeypatch):
    from app.models import OpenAISettings, User

    admin = User(username="openerr", email="oe@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    # Set API key so endpoint proceeds to call OpenAI
    settings = OpenAISettings(id=1, api_key="sk-test")
    db_session.add(settings)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    class FakeAsyncOpenAI:
        def __init__(self, api_key=None):
            self.api_key = api_key

        class Models:
            @staticmethod
            async def list():
                raise Exception("service down")

        @property
        def models(self):
            return self.Models

    monkeypatch.setattr("openai.AsyncOpenAI", FakeAsyncOpenAI)

    resp = await client.get("/api/v1/admin/openai-models", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
