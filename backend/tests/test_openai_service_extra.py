import pytest

from app.models import Recipe, RecipeTag
from app.services.openai_service import OpenAIService


@pytest.mark.asyncio
async def test_categorize_tag(db_session):
    service = OpenAIService(db_session)
    assert service._categorize_tag("vegan") == "dietary"
    assert service._categorize_tag("italian") == "cuisine"
    assert service._categorize_tag("dinner") == "meal_type"
    assert service._categorize_tag("baking") == "cooking_method"
    assert service._categorize_tag("something-else") == "other"


@pytest.mark.asyncio
async def test_create_recipe_validation_errors(db_session, test_user):
    service = OpenAIService(db_session)

    # Ingredient as non-dict
    with pytest.raises(ValueError):
        await service.create_recipe({"name": "X", "ingredients": ["invalid"], "instructions": ["a"], "prep_time": 1, "cook_time": 1, "servings": 1}, test_user)

    # Missing numeric quantity
    with pytest.raises(ValueError):
        await service.create_recipe({"name": "X", "ingredients": [{"name": "salt", "unit": "tsp"}], "instructions": ["a"], "prep_time": 1, "cook_time": 1, "servings": 1}, test_user)

    # Name contains measurements
    with pytest.raises(ValueError):
        await service.create_recipe({"name": "X", "ingredients": [{"name": "1/2 tsp sugar", "quantity": 1, "unit": "tsp"}], "instructions": ["a"], "prep_time": 1, "cook_time": 1, "servings": 1}, test_user)


@pytest.mark.asyncio
async def test_create_recipe_with_tags_and_placeholder_image(db_session, test_user, monkeypatch):
    service = OpenAIService(db_session)

    async def fake_search_images(query, max_results=1):
        return []

    monkeypatch.setattr(service, "search_images", fake_search_images)

    data = {
        "name": "AI Dish",
        "ingredients": [{"name": "salt", "quantity": 1, "unit": "tsp"}],
        "instructions": ["do it"],
        "prep_time": 5,
        "cook_time": 10,
        "servings": 2,
        "tags": ["vegan", "italian"],
    }

    recipe = await service.create_recipe(data, test_user)
    assert recipe.title == "AI Dish"

    # tags should have been created
    tags_result = await db_session.execute(RecipeTag.__table__.select().where(RecipeTag.recipe_id == recipe.id))
    tags = tags_result.all()
    assert len(tags) == 2


@pytest.mark.asyncio
async def test_update_recipe_and_replace_tags(db_session, test_user):
    # create initial recipe
    r = Recipe(title="Old", owner_id=test_user.id, ingredients=[{"name": "salt", "quantity": 1, "unit": "tsp"}], instructions=["ok"], prep_time=1, cook_time=1, serving_size=1)
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    service = OpenAIService(db_session)

    update = {"recipe_id": r.id, "name": "New", "tags": ["dessert", "baking"]}
    updated = await service.update_recipe(update, test_user)

    assert updated.title == "New"

    tags_result = await db_session.execute(RecipeTag.__table__.select().where(RecipeTag.recipe_id == r.id))
    tags = tags_result.all()
    assert len(tags) == 2


@pytest.mark.asyncio
async def test_search_web_and_fetch_url(monkeypatch):
    class FakeResp:
        def __init__(self, json_data=None, text="", status=200):
            self._json = json_data or {}
            self.text = text
            self.status_code = status
            self.headers = {"content-type": "text/html"}

        def json(self):
            return self._json

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception("bad")

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params=None, headers=None):
            if "format" in (params or {}):
                # search_web
                return FakeResp(json_data={"results": [{"title": "R", "url": "http://x", "content": "c"}]})
            else:
                # fetch_url
                html = "<html><head><title>Test</title></head><body><article><p>some content</p></article></body></html>"
                return FakeResp(text=html)

    monkeypatch.setattr("app.services.openai_service.httpx.AsyncClient", FakeClient)

    # Provide a minimal BeautifulSoup implementation when beautifulsoup4 is not available
    try:
        from bs4 import BeautifulSoup as bs  # noqa: F401, N813
    except Exception:
        import re

        class FakeSoup:
            def __init__(self, text, parser):
                self._text = text
                m = re.search(r'<title>(.*?)</title>', text, re.I | re.S)
                self.title = type('T', (), {'string': m.group(1)}) if m else None

            def find(self, name, *args, **kwargs):
                if name == 'script' and kwargs.get('type') == 'application/ld+json':
                    return None
                if name == 'article':
                    class A:
                        def __init__(self, outer):
                            self._text = outer._text

                        def find_all(self, *a, **k):
                            return []

                        def get_text(self, separator="\n", strip=True):
                            import re

                            return re.sub(r'<[^>]+>', '', self._text)

                    return A(self)
                return None

            def find_all(self, names):
                return []

            def get_text(self, separator="\n", strip=True):
                import re

                return re.sub(r'<[^>]+>', '', self._text)

        monkeypatch.setattr("app.services.openai_service.BeautifulSoup", FakeSoup)

    # instantiate service and call methods
    from app.services.openai_service import OpenAIService

    # search_web
    service = OpenAIService(None)
    res = await service.search_web("foo", max_results=1)
    assert isinstance(res, list) and res[0]["title"] == "R"

    # fetch_url
    fetched = await service.fetch_url("http://example.com")
    assert fetched["title"] == "Test"
    assert "some content" in fetched["content"]
