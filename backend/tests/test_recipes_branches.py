import io
import pytest
from datetime import datetime
from app.models import User, Recipe, RecipeTag, Group, GroupMember, UserFavorite
from app.utils.auth import create_access_token


@pytest.mark.asyncio
async def test_list_recipes_tags_and_dietary(client, db_session, test_user, test_token):
    # create recipes with tags
    r1 = Recipe(title="Taggy", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    r2 = Recipe(title="Plain", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    db_session.add_all([r1, r2])
    await db_session.commit()
    await db_session.refresh(r1)

    tag = RecipeTag(recipe_id=r1.id, tag_name="vegan", tag_category="diet")
    db_session.add(tag)
    await db_session.commit()

    # tag filter
    resp = await client.get("/api/v1/recipes?tags=vegan", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert any(item["title"] == "Taggy" for item in data["items"])

    # dietary legacy filter
    resp2 = await client.get("/api/v1/recipes?dietary=vegan", headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 200
    assert any(item["title"] == "Taggy" for item in resp2.json()["items"])


@pytest.mark.asyncio
async def test_group_visibility_and_permissions(client, db_session, test_user, test_token):
    # create group and recipe
    g = Group(name="G1", owner_id=test_user.id)
    db_session.add(g)
    await db_session.commit()
    await db_session.refresh(g)

    # recipe visible to group
    r = Recipe(title="GRecipe", owner_id=test_user.id, visibility="group", group_id=g.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # other user initially cannot access
    other = User(username="o2", email="o2@example.com", password_hash="x")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)
    other_token = create_access_token({"sub": str(other.id)})

    resp = await client.get(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {other_token}"})
    assert resp.status_code == 403

    # add membership and try again
    gm = GroupMember(group_id=g.id, user_id=other.id, role="member")
    db_session.add(gm)
    await db_session.commit()

    resp2 = await client.get(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {other_token}"})
    assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_update_and_delete_permissions(client, db_session, test_user, test_token):
    # create other user and recipe
    other = User(username="otherx", email="otherx@example.com", password_hash="x")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    r = Recipe(title="ToEdit", owner_id=other.id, ingredients=[], instructions=[], visibility="private")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # test update as non-owner -> 403
    resp = await client.put(f"/api/v1/recipes/{r.id}", json={"title": "X"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 403

    # admin can delete
    admin = User(username="admx", email="admx@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    await db_session.commit()
    token_admin = create_access_token({"sub": str(admin.id)})

    resp2 = await client.delete(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {token_admin}"})
    assert resp2.status_code == 204


@pytest.mark.asyncio
async def test_upload_image_io_failure_returns_500(client, db_session, test_user, test_token, monkeypatch):
    # create recipe
    r = Recipe(title="ImgFail", owner_id=test_user.id, ingredients=[], instructions=[], visibility="private")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    class BadFile:
        filename = "bad.jpg"
        content_type = "image/jpeg"

        async def read(self):
            raise IOError("disk full")

    # monkeypatch UploadFile read by passing BadFile via files param may not work; instead call endpoint directly via starlette TestClient simulation
    files = {"file": ("bad.jpg", io.BytesIO(b"x"), "image/jpeg")}

    # monkeypatch the open/write to raise
    def raise_open(*args, **kwargs):
        raise IOError("disk full")

    monkeypatch.setattr("builtins.open", raise_open)

    resp = await client.post(f"/api/v1/recipes/{r.id}/image", files=files, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_get_all_tags_grouping(client, db_session, test_user, test_token):
    r1 = Recipe(title="T1", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r1)
    await db_session.commit()
    await db_session.refresh(r1)

    t1 = RecipeTag(recipe_id=r1.id, tag_name="tomato", tag_category="veg")
    t2 = RecipeTag(recipe_id=r1.id, tag_name="basil", tag_category=None)
    db_session.add_all([t1, t2])
    await db_session.commit()

    resp = await client.get("/api/v1/recipes/tags/all", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "veg" in data
    assert "other" in data


@pytest.mark.asyncio
async def test_calculate_nutrition_missing_recipe(client):
    resp = await client.get("/api/v1/recipes/9999/nutrition")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_favorites_endpoint(client, db_session, test_user, test_token):
    r = Recipe(title="FavIt", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # add favorite
    uf = UserFavorite(user_id=test_user.id, recipe_id=r.id)
    db_session.add(uf)
    await db_session.commit()

    resp = await client.get("/api/v1/recipes/favorites", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert any(item["id"] == r.id for item in resp.json())
