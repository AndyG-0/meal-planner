import pytest
from app.models import Recipe, RecipeTag, User, UserFavorite
from app.utils.auth import create_access_token
import io


@pytest.mark.asyncio
async def test_list_recipes_cleans_ingredients_and_includes_tags(client, db_session, test_user, test_token):
    # create recipe with messy ingredient name
    r = Recipe(title="CleanR", owner_id=test_user.id, category="dinner", visibility="public", ingredients=[{"name": "1 cup flour", "quantity": None, "unit": ""}], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # add tag
    t = RecipeTag(recipe_id=r.id, tag_name="baking", tag_category="tech")
    db_session.add(t)
    await db_session.commit()

    resp = await client.get("/api/v1/recipes", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    found = next((it for it in items if it["title"] == "CleanR"), None)
    assert found is not None
    assert any(ing["name"] == "flour" or "flour" in ing["name"] for ing in found["ingredients"]) 
    assert any(tg["tag_name"] == "baking" for tg in found["tags"]) 


@pytest.mark.asyncio
async def test_admin_list_recipes_includes_owner_username(client, db_session):
    admin = User(username="adlist", email="adlist@example.com", password_hash="x", is_admin=True)
    owner = User(username="ownr", email="ownr@example.com", password_hash="x")
    db_session.add_all([admin, owner])
    await db_session.commit()
    await db_session.refresh(owner)

    r = Recipe(title="AR1", owner_id=owner.id, visibility="public", ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})
    resp = await client.get("/api/v1/admin/recipes", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(item["owner_username"] == "ownr" for item in resp.json())