import pytest
from app.utils.auth import create_access_token
from app.models import User, Recipe, RecipeTag


@pytest.mark.asyncio
async def test_admin_get_and_update_and_delete_recipe(client, db_session):
    admin = User(username="adm3", email="adm3@example.com", password_hash="x", is_admin=True)
    u = User(username="ru2", email="ru2@example.com", password_hash="x")
    db_session.add_all([admin, u])
    await db_session.commit()
    await db_session.refresh(u)

    r = Recipe(title="AdmR", owner_id=u.id, ingredients=[{"name": "(100 g) cheese"}], instructions=["do"], category="snack")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    token = create_access_token({"sub": str(admin.id)})

    # get details
    resp = await client.get(f"/api/v1/admin/recipes/{r.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == r.id
    assert "ingredients" in data

    # update recipe as admin
    resp2 = await client.patch(f"/api/v1/admin/recipes/{r.id}", json={"title": "AdmR2", "category": "snack"}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    updated = resp2.json()
    assert updated["title"] == "AdmR2"

    # delete recipe
    resp3 = await client.delete(f"/api/v1/admin/recipes/{r.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 204

    # now details should 404
    resp4 = await client.get(f"/api/v1/admin/recipes/{r.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp4.status_code == 404


@pytest.mark.asyncio
async def test_get_all_tags_grouping(client, db_session, test_user, test_token):
    # create tags on a public recipe and a private recipe
    r1 = Recipe(title="T1", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    r2 = Recipe(title="T2", owner_id=test_user.id, ingredients=[], instructions=[], visibility="private")
    db_session.add_all([r1, r2])
    await db_session.commit()

    t1 = RecipeTag(recipe_id=r1.id, tag_name="vegan", tag_category="diet")
    t2 = RecipeTag(recipe_id=r2.id, tag_name="quick", tag_category=None)
    db_session.add_all([t1, t2])
    await db_session.commit()

    resp = await client.get("/api/v1/recipes/tags/all", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "diet" in data and any(x["name"] == "vegan" for x in data["diet"]) or "other" in data
