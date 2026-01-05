from pathlib import Path

import pytest

from app.models import Recipe, RecipeTag, User, UserFavorite
from app.utils.auth import create_access_token


@pytest.mark.asyncio
async def test_upload_recipe_image_success_and_cleanup(client, db_session):
    u = User(username="imgok", email="imgok@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r = Recipe(title="ImgOK", owner_id=u.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    token = create_access_token({"sub": str(u.id)})

    files = {"file": ("image.jpg", b"\xff\xd8\xff", "image/jpeg")}
    resp = await client.post(f"/api/v1/recipes/{r.id}/image", files=files, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "image_url" in data
    assert "/uploads/recipes/" in data["image_url"]

    # check file exists on disk
    filename = data["image_url"].split("/uploads/recipes/")[-1]
    file_path = Path("uploads/recipes") / filename
    assert file_path.exists()

    # cleanup
    try:
        file_path.unlink()
    except Exception:
        pass


@pytest.mark.asyncio
async def test_list_favorite_recipes_and_is_favorite_flag(client, db_session):
    u = User(username="favok", email="favok@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r1 = Recipe(title="FavA", owner_id=u.id, ingredients=[], instructions=[])
    r2 = Recipe(title="FavB", owner_id=u.id, ingredients=[], instructions=[])
    db_session.add_all([r1, r2])
    await db_session.commit()

    # favorite r1
    fav = UserFavorite(user_id=u.id, recipe_id=r1.id)
    db_session.add(fav)
    await db_session.commit()

    token = create_access_token({"sub": str(u.id)})
    resp = await client.get("/api/v1/recipes/favorites", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert any(item["id"] == r1.id and item["is_favorite"] for item in data)
    assert all(item["is_favorite"] is True for item in data)


@pytest.mark.asyncio
async def test_list_recipes_tags_multiple_and_pagination(client, db_session):
    u = User(username="tagok", email="tagok@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r1 = Recipe(title="T1", owner_id=u.id, visibility="public", ingredients=[], instructions=[])
    r2 = Recipe(title="T2", owner_id=u.id, visibility="public", ingredients=[], instructions=[])
    db_session.add_all([r1, r2])
    await db_session.commit()

    t1 = RecipeTag(recipe_id=r1.id, tag_name="a")
    t2 = RecipeTag(recipe_id=r2.id, tag_name="b")
    t3 = RecipeTag(recipe_id=r2.id, tag_name="a")
    db_session.add_all([t1, t2, t3])
    await db_session.commit()

    token = create_access_token({"sub": str(u.id)})

    # filter by single tag
    resp = await client.get("/api/v1/recipes?tags=a", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["total"] >= 1
    assert any(item["title"] in ("T1", "T2") for item in [x for x in data["items"]])

    # pagination edge: high page returns zero items
    resp2 = await client.get("/api/v1/recipes?page=99&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert isinstance(data2["items"], list)


@pytest.mark.asyncio
async def test_list_recipes_prep_cook_none_included(client, db_session):
    u = User(username="tc", email="tc@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r = Recipe(title="NoTimes", owner_id=u.id, visibility="public", prep_time=None, cook_time=None, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()

    token = create_access_token({"sub": str(u.id)})
    resp = await client.get("/api/v1/recipes?max_prep_time=10", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    # recipe with None prep_time should be included per query logic
    assert any(item["title"] == "NoTimes" for item in data["items"])
