import types

import pytest
from pytest import MonkeyPatch


@pytest.mark.asyncio
async def test_ai_status_available(client, test_user, monkeypatch: MonkeyPatch):
    from app.api.v1.endpoints import ai as ai_module

    class FakeOpenAI:
        def __init__(self, db):
            self.db = db
            self.settings = types.SimpleNamespace(model="gpt-4")

        async def initialize(self):
            # leave settings as-is
            return

    monkeypatch.setattr(ai_module, "OpenAIService", FakeOpenAI)

    resp = await client.get("/api/v1/ai/status", headers={"Authorization": f"Bearer {await _get_token(client, test_user)}"})
    assert resp.status_code == 200
    assert resp.json()["available"] is True
    assert resp.json()["model"] == "gpt-4"


@pytest.mark.asyncio
async def test_ai_chat_success(client, test_user, monkeypatch: MonkeyPatch):
    from app.api.v1.endpoints import ai as ai_module

    class FakeOpenAI:
        def __init__(self, db):
            self.db = db

        async def initialize(self):
            return

        async def chat(self, messages, current_user, use_dietary_preferences):
            return {"message": "OK", "tool_calls": [{"id": "1", "name": "list_user_recipes", "arguments": {}}]}

    monkeypatch.setattr(ai_module, "OpenAIService", FakeOpenAI)

    payload = {"messages": [{"role": "user", "content": "Hi"}], "use_dietary_preferences": False}
    token = await _get_token(client, test_user)
    resp = await client.post("/api/v1/ai/chat", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("message") == "OK"
    assert isinstance(data.get("tool_calls"), list)


@pytest.mark.asyncio
async def test_execute_tool_list_and_unknown(client, test_user, monkeypatch: MonkeyPatch):
    from app.api.v1.endpoints import ai as ai_module

    class FakeOpenAI:
        def __init__(self, db):
            self.db = db

        async def initialize(self):
            return

        async def list_user_recipes(self, current_user, limit):
            return [{"id": 1, "title": "R1"}, {"id": 2, "title": "R2"}]

    monkeypatch.setattr(ai_module, "OpenAIService", FakeOpenAI)

    token = await _get_token(client, test_user)

    # list
    resp = await client.post(
        "/api/v1/ai/execute-tool",
        json={"name": "list_user_recipes", "arguments": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "list"
    assert isinstance(body["recipes"], list)

    # unknown
    resp2 = await client.post(
        "/api/v1/ai/execute-tool",
        json={"name": "this_does_not_exist", "arguments": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_execute_tool_create_recipe_end_to_end(client, test_user, db_session, monkeypatch: MonkeyPatch):
    from app.api.v1.endpoints import ai as ai_module
    from app.models import Recipe

    class FakeOpenAI:
        def __init__(self, db):
            self.db = db

        async def initialize(self):
            return

        async def create_recipe(self, arguments, current_user):
            r = Recipe(
                title=arguments.get("title", "AI Recipe"),
                owner_id=current_user.id,
                ingredients=[{"name": "salt", "quantity": 1, "unit": "tsp"}],
                instructions=["do it"],
            )
            self.db.add(r)
            await self.db.commit()
            await self.db.refresh(r)
            return r

    monkeypatch.setattr(ai_module, "OpenAIService", FakeOpenAI)

    token = await _get_token(client, test_user)

    payload = {"name": "create_recipe", "arguments": {"title": "From AI"}}
    resp = await client.post("/api/v1/ai/execute-tool", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "create"
    assert body["success"] is True
    assert "recipe" in body
    assert body["recipe"]["title"] == "From AI"


@pytest.mark.asyncio
async def test_image_search_and_fetch_url(client, test_user, monkeypatch: MonkeyPatch):
    from app.api.v1.endpoints import ai as ai_module

    class FakeOpenAI:
        def __init__(self, db):
            self.db = db

        async def initialize(self):
            return

        async def search_images(self, query, max_results):
            return [{"title": "img1", "url": "http://img"}]

        async def fetch_url(self, url):
            return {"url": url, "content": "hello"}

    monkeypatch.setattr(ai_module, "OpenAIService", FakeOpenAI)

    token = await _get_token(client, test_user)

    resp = await client.get("/api/v1/ai/search-images", params={"query": "pizza"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    resp2 = await client.post(
        "/api/v1/ai/execute-tool",
        json={"name": "fetch_url", "arguments": {"url": "http://example.com"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["action"] == "fetch"
    assert resp2.json()["content"]["content"] == "hello"


async def _get_token(client, test_user):
    resp = await client.post("/api/v1/auth/login", data={"username": test_user.username, "password": "password"})
    assert resp.status_code == 200
    return resp.json().get("access_token")
