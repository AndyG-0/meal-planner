import pytest
from app.models import Recipe, RecipeTag


@pytest.mark.asyncio
async def test_list_recipes_search_and_filters(client, test_user, test_token, db_session):
    r1 = Recipe(title="UniqueTitleX", owner_id=test_user.id, category="dinner", prep_time=10, cook_time=5, difficulty="easy", visibility="public", ingredients=[], instructions=[])
    r2 = Recipe(title="Other", owner_id=test_user.id, category="dinner", prep_time=60, cook_time=30, difficulty="hard", visibility="public", ingredients=[], instructions=[])
    db_session.add_all([r1, r2])
    await db_session.commit()

    # Search
    resp = await client.get("/api/v1/recipes?search=UniqueTitleX", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any("UniqueTitleX" == it["title"] for it in items)

    # Difficulty filter
    resp = await client.get("/api/v1/recipes?difficulty=hard", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(it["difficulty"] == "hard" for it in items)

    # Max prep time
    resp = await client.get("/api/v1/recipes?max_prep_time=30", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all((it.get("prep_time") is None) or (it.get("prep_time") <= 30) for it in items)


@pytest.mark.asyncio
async def test_list_recipes_tags_and_dietary(client, test_user, test_token, db_session):
    r = Recipe(title="Taggy", owner_id=test_user.id, category="lunch", prep_time=5, visibility="public", ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # Add tag
    t = RecipeTag(recipe_id=r.id, tag_name="vegan", tag_category="dietary")
    db_session.add(t)
    await db_session.commit()

    # Filter by tags
    resp = await client.get("/api/v1/recipes?tags=vegan", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(it["title"] == "Taggy" for it in items)

    # Use deprecated dietary param
    resp2 = await client.get("/api/v1/recipes?dietary=vegan", headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 200
    items2 = resp2.json()["items"]
    assert any(it["title"] == "Taggy" for it in items2)


@pytest.mark.asyncio
async def test_get_all_tags_empty_and_nonempty(client, test_user, test_token, db_session):
    # Ensure empty initially (may have other tests, so create a unique tag and then clean)
    resp_empty = await client.get("/api/v1/recipes/tags/all", headers={"Authorization": f"Bearer {test_token}"})
    assert resp_empty.status_code == 200
    assert isinstance(resp_empty.json(), dict)

    # Add a tag and ensure it shows up
    r = Recipe(title="TTag", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    t = RecipeTag(recipe_id=r.id, tag_name="searchtag", tag_category="other")
    db_session.add(t)
    await db_session.commit()

    resp = await client.get("/api/v1/recipes/tags/all", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert any(item["name"] == "searchtag" for vals in data.values() for item in vals)
