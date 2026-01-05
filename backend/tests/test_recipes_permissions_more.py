import pytest
from sqlalchemy import select
from app.utils.auth import create_access_token
from app.models import User, Recipe, Group, GroupMember, RecipeTag


@pytest.mark.asyncio
async def test_update_and_delete_recipe_owner_and_group_admin(client, db_session):
    owner = User(username="own3", email="own3@example.com", password_hash="x")
    other = User(username="other3", email="other3@example.com", password_hash="x")
    db_session.add_all([owner, other])
    await db_session.commit()
    await db_session.refresh(owner)
    await db_session.refresh(other)

    grp = Group(name="G2", owner_id=owner.id)
    db_session.add(grp)
    await db_session.commit()
    await db_session.refresh(grp)

    # group recipe owned by owner
    r = Recipe(title="UpdateR", owner_id=owner.id, visibility="group", group_id=grp.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # other is not member and cannot update
    token_other = create_access_token({"sub": str(other.id)})
    resp = await client.put(f"/api/v1/recipes/{r.id}", json={"title": "X"}, headers={"Authorization": f"Bearer {token_other}"})
    assert resp.status_code == 403

    # add other as group admin and now can edit
    gm = GroupMember(group_id=grp.id, user_id=other.id, role="admin")
    db_session.add(gm)
    await db_session.commit()

    resp2 = await client.put(f"/api/v1/recipes/{r.id}", json={"title": "X"}, headers={"Authorization": f"Bearer {token_other}"})
    assert resp2.status_code == 200
    assert resp2.json()["title"] == "X"

    # owner can delete
    token_owner = create_access_token({"sub": str(owner.id)})
    resp3 = await client.delete(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {token_owner}"})
    assert resp3.status_code == 204

    # now get -> 404
    resp4 = await client.get(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {token_owner}"})
    assert resp4.status_code == 404


@pytest.mark.asyncio
async def test_list_recipes_category_difficulty_and_dietary_filters(client, db_session):
    u = User(username="filteru", email="filter@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r1 = Recipe(title="CatA", owner_id=u.id, visibility="public", category="dessert", difficulty="easy", ingredients=[], instructions=[])
    r2 = Recipe(title="CatB", owner_id=u.id, visibility="public", category="dinner", difficulty="hard", ingredients=[], instructions=[])
    db_session.add_all([r1, r2])
    await db_session.commit()

    # add dietary tag to r2
    t = RecipeTag(recipe_id=r2.id, tag_name="vegan")
    db_session.add(t)
    await db_session.commit()

    token = create_access_token({"sub": str(u.id)})

    resp = await client.get("/api/v1/recipes?category=dessert", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(item["title"] == "CatA" for item in resp.json()["items"]) 

    resp2 = await client.get("/api/v1/recipes?difficulty=hard", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    assert any(item["title"] == "CatB" for item in resp2.json()["items"]) 

    resp3 = await client.get("/api/v1/recipes?dietary=vegan", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 200
    assert any(item["title"] == "CatB" for item in resp3.json()["items"]) 


@pytest.mark.asyncio
async def test_list_recipes_group_visibility_requires_membership(client, db_session):
    owner = User(username="gowner", email="gowner@example.com", password_hash="x")
    other = User(username="gother", email="gother@example.com", password_hash="x")
    db_session.add_all([owner, other])
    await db_session.commit()
    await db_session.refresh(owner)
    await db_session.refresh(other)

    grp = Group(name="G3", owner_id=owner.id)
    db_session.add(grp)
    await db_session.commit()
    await db_session.refresh(grp)

    r = Recipe(title="GroupOnly", owner_id=owner.id, visibility="group", group_id=grp.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()

    token_other = create_access_token({"sub": str(other.id)})
    # other not a member -> should not see the recipe
    resp = await client.get("/api/v1/recipes", headers={"Authorization": f"Bearer {token_other}"})
    assert resp.status_code == 200
    assert all(item["title"] != "GroupOnly" for item in resp.json()["items"])

    # add membership and now the recipe should appear
    gm = GroupMember(group_id=grp.id, user_id=other.id, role="member")
    db_session.add(gm)
    await db_session.commit()

    resp2 = await client.get("/api/v1/recipes", headers={"Authorization": f"Bearer {token_other}"})
    assert resp2.status_code == 200
    assert any(item["title"] == "GroupOnly" for item in resp2.json()["items"])