import io

import pytest

from app.models import Group, GroupMember, Recipe, RecipeTag, User


@pytest.mark.asyncio
async def test_list_recipes_pagination_and_filters(client, db_session, test_user, test_token):
    # create multiple recipes
    r1 = Recipe(title="P1", owner_id=test_user.id, category="dinner", prep_time=10, cook_time=20, visibility="public", ingredients=[], instructions=[])
    r2 = Recipe(title="P2", owner_id=test_user.id, category="breakfast", prep_time=5, cook_time=0, visibility="public", ingredients=[], instructions=[])
    r3 = Recipe(title="SearchMe", owner_id=test_user.id, category="dinner", prep_time=30, cook_time=10, visibility="public", ingredients=[], instructions=[], description="special")
    db_session.add_all([r1, r2, r3])
    await db_session.commit()

    # page size 2
    resp = await client.get("/api/v1/recipes?page=1&page_size=2", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 2

    # search by description
    resp2 = await client.get("/api/v1/recipes?search=special", headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 200
    assert any(item["title"] == "SearchMe" for item in resp2.json()["items"])

    # category filter
    resp3 = await client.get("/api/v1/recipes?category=breakfast", headers={"Authorization": f"Bearer {test_token}"})
    assert resp3.status_code == 200
    assert all(item["category"] == "breakfast" for item in resp3.json()["items"])

    # max_prep_time filter
    resp4 = await client.get("/api/v1/recipes?max_prep_time=10", headers={"Authorization": f"Bearer {test_token}"})
    assert resp4.status_code == 200
    assert all((item.get("prep_time") is None or item["prep_time"] <= 10) for item in resp4.json()["items"])


@pytest.mark.asyncio
async def test_tags_filter_and_get_all_tags(client, db_session, test_user, test_token):
    r1 = Recipe(title="T1", owner_id=test_user.id, category="dinner", visibility="public", ingredients=[], instructions=[])
    r2 = Recipe(title="T2", owner_id=test_user.id, category="dinner", visibility="public", ingredients=[], instructions=[])
    db_session.add_all([r1, r2])
    await db_session.commit()
    await db_session.refresh(r1)
    await db_session.refresh(r2)

    # add tags
    t1 = RecipeTag(recipe_id=r1.id, tag_name="a", tag_category="x")
    t2 = RecipeTag(recipe_id=r2.id, tag_name="b", tag_category="x")
    db_session.add_all([t1, t2])
    await db_session.commit()

    # filter by tag a
    resp = await client.get("/api/v1/recipes?tags=a", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert any(item["title"] == "T1" for item in resp.json()["items"])

    # get all tags
    resp2 = await client.get("/api/v1/recipes/tags/all", headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 200
    data = resp2.json()
    assert "x" in data


@pytest.mark.asyncio
async def test_group_visibility_and_update_by_admin(client, db_session, test_user, test_token):
    # create group and group recipe owned by other user
    other = User(username="gowner", email="gowner@example.com", password_hash="x")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    g = Group(name="GTest", owner_id=other.id)
    db_session.add(g)
    await db_session.commit()
    await db_session.refresh(g)

    r = Recipe(title="GroupRec", owner_id=other.id, category="dinner", visibility="group", group_id=g.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # test_user is not in group, cannot access
    resp = await client.get(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 403

    # make test_user a group admin and retry
    gm = GroupMember(group_id=g.id, user_id=test_user.id, role="admin")
    db_session.add(gm)
    await db_session.commit()

    resp2 = await client.get(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 200

    # group admin can update group recipe (owner check)
    resp3 = await client.put(f"/api/v1/recipes/{r.id}", json={"title": "GUpdated"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp3.status_code in (200, 201)


@pytest.mark.asyncio
async def test_import_with_item_error_reports(client, db_session, test_user, test_token):
    # import with one valid and one invalid recipe
    valid = {"title": "I1", "ingredients": [], "instructions": []}
    invalid = {"ingredients": [], "instructions": []}  # missing title
    payload = [valid, invalid]

    files = {"file": ("data.json", io.BytesIO(__import__('json').dumps(payload).encode()), "application/json")}

    resp = await client.post("/api/v1/recipes/import", files=files, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["errors"] is not None
    assert any("Missing required fields" in e for e in data["errors"])
