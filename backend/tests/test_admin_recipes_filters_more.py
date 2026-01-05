import pytest
from app.utils.auth import create_access_token
from app.models import User, Recipe, RecipeTag


@pytest.mark.asyncio
async def test_admin_list_recipes_filters_and_search(client, db_session):
    admin = User(username="radm", email="radm@example.com", password_hash="x", is_admin=True)
    u = User(username="ownerx", email="ownerx@example.com", password_hash="x")
    db_session.add_all([admin, u])
    await db_session.commit()
    await db_session.refresh(u)

    r1 = Recipe(title="AS1", owner_id=u.id, visibility="public", category="dessert", difficulty="easy", ingredients=[], instructions=[])
    r2 = Recipe(title="AS2", owner_id=u.id, visibility="private", category="dinner", difficulty="hard", ingredients=[], instructions=[])
    r3 = Recipe(title="SearchMeAdmin", owner_id=u.id, visibility="public", ingredients=[], instructions=[])
    db_session.add_all([r1, r2, r3])
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    resp = await client.get("/api/v1/admin/recipes?visibility=public", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(item["visibility"] == "public" for item in resp.json())

    resp2 = await client.get("/api/v1/admin/recipes?category=dinner", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    assert any(item["title"] == "AS2" for item in resp2.json())

    resp3 = await client.get("/api/v1/admin/recipes?search=SearchMeAdmin", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 200
    assert any(item["title"] == "SearchMeAdmin" for item in resp3.json())


@pytest.mark.asyncio
async def test_admin_get_recipe_404_and_owner_username_present(client, db_session):
    admin = User(username="radm2", email="radm2@example.com", password_hash="x", is_admin=True)
    u = User(username="owner2", email="owner2@example.com", password_hash="x")
    db_session.add_all([admin, u])
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    # not found
    resp = await client.get("/api/v1/admin/recipes/99999", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404

    # create one and ensure owner_username is returned
    r = Recipe(title="OwnerBack", owner_id=u.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    resp2 = await client.get(f"/api/v1/admin/recipes/{r.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    assert resp2.json()["owner_username"] == u.username