import pytest
from app.utils.auth import create_access_token
from app.models import User, Recipe, RecipeTag


@pytest.mark.asyncio
async def test_list_recipes_search_and_multi_tag(client, db_session):
    u = User(username="searchu", email="search@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r1 = Recipe(title="SearchMe", owner_id=u.id, visibility="public", ingredients=[], instructions=[])
    r2 = Recipe(title="TagA", owner_id=u.id, visibility="public", ingredients=[], instructions=[])
    r3 = Recipe(title="TagB", owner_id=u.id, visibility="public", ingredients=[], instructions=[])
    db_session.add_all([r1, r2, r3])
    await db_session.commit()

    t1 = RecipeTag(recipe_id=r2.id, tag_name="a")
    t2 = RecipeTag(recipe_id=r3.id, tag_name="b")
    db_session.add_all([t1, t2])
    await db_session.commit()

    token = create_access_token({"sub": str(u.id)})

    # search
    resp = await client.get("/api/v1/recipes?search=SearchMe", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(item["title"] == "SearchMe" for item in resp.json()["items"]) 

    # multi-tags
    resp2 = await client.get("/api/v1/recipes?tags=a,b", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    titles = [x["title"] for x in resp2.json()["items"]]
    assert "TagA" in titles and "TagB" in titles


@pytest.mark.asyncio
async def test_get_all_tags_user_grouping(client, db_session):
    u = User(username="tagu2", email="tagu2@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r1 = Recipe(title="Tg1", owner_id=u.id, visibility="public", ingredients=[], instructions=[])
    r2 = Recipe(title="Tg2", owner_id=u.id, visibility="public", ingredients=[], instructions=[])
    db_session.add_all([r1, r2])
    await db_session.commit()

    t1 = RecipeTag(recipe_id=r1.id, tag_name="veggie", tag_category="diet")
    t2 = RecipeTag(recipe_id=r2.id, tag_name="fast", tag_category=None)
    db_session.add_all([t1, t2])
    await db_session.commit()

    token = create_access_token({"sub": str(u.id)})
    resp = await client.get("/api/v1/recipes/tags/all", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert ("diet" in data and any(x["name"] == "veggie" for x in data["diet"])) or ("other" in data and any(x["name"] == "fast" for x in data.get("other", [])))


@pytest.mark.asyncio
async def test_owner_update_recipe_success(client, db_session):
    u = User(username="ownup", email="ownup@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r = Recipe(title="OwnUp", owner_id=u.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    token = create_access_token({"sub": str(u.id)})
    resp = await client.put(f"/api/v1/recipes/{r.id}", json={"title": "OwnUp2"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "OwnUp2"