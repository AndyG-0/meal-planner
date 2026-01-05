import pytest

from app.models import Recipe, RecipeTag, User
from app.utils.auth import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_admin_recipe_list_get_patch_delete(client, db_session):
    # create admin
    admin = User(username="aread", email="a@example.com", password_hash=get_password_hash("p"), is_admin=True)
    db_session.add(admin)

    # create user and recipe
    u = User(username="rowner", email="r@example.com", password_hash=get_password_hash("p"))
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r = Recipe(title="AdmR", owner_id=u.id, ingredients=[], instructions=[], category="dinner", visibility="public")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    token = create_access_token({"sub": str(admin.id)})

    # List recipes via admin endpoint
    resp = await client.get("/api/v1/admin/recipes?category=dinner", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(item["title"] == "AdmR" for item in resp.json())

    # Get details
    resp = await client.get(f"/api/v1/admin/recipes/{r.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "AdmR"

    # Patch
    resp = await client.patch(f"/api/v1/admin/recipes/{r.id}", json={"title": "AdmR2"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "AdmR2"

    # Delete
    resp = await client.delete(f"/api/v1/admin/recipes/{r.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_tags_all_grouping(client, db_session, test_user, test_token):
    # create two recipes with tags
    r1 = Recipe(title="T1", owner_id=test_user.id, ingredients=[], instructions=[])
    r2 = Recipe(title="T2", owner_id=test_user.id, ingredients=[], instructions=[])
    db_session.add_all([r1, r2])
    await db_session.commit()
    await db_session.refresh(r1)
    await db_session.refresh(r2)

    tag1 = RecipeTag(recipe_id=r1.id, tag_name="vegan", tag_category="dietary")
    tag2 = RecipeTag(recipe_id=r2.id, tag_name="italian", tag_category="cuisine")
    db_session.add_all([tag1, tag2])
    await db_session.commit()

    resp = await client.get("/api/v1/recipes/tags/all", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "dietary" in data and any(t["name"] == "vegan" for t in data["dietary"]) or any(t["name"] == "vegan" for k in data.values() for t in k)
