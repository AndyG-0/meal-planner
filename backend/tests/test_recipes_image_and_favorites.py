import io
import json
import builtins
import pytest
from app.utils.auth import create_access_token
from app.models import User, Recipe, UserFavorite, RecipeRating


@pytest.mark.asyncio
async def test_upload_recipe_image_valid_and_invalid(client, db_session, tmp_path):
    u = User(username="imguser", email="img@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r = Recipe(title="ImgR", owner_id=u.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    token = create_access_token({"sub": str(u.id)})

    # non-image file -> 400
    files = {"file": ("notimage.txt", b"data", "text/plain")}
    resp = await client.post(f"/api/v1/recipes/{r.id}/image", files=files, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_upload_recipe_image_save_failure(monkeypatch, client, db_session):
    # Setup user and recipe
    u = User(username="imguser2", email="img2@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r = Recipe(title="ImgR2", owner_id=u.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    token = create_access_token({"sub": str(u.id)})

    # Monkeypatch builtins.open to raise when trying to write file
    def fake_open(*args, **kwargs):
        raise IOError("disk full")

    monkeypatch.setattr(builtins, "open", fake_open, raising=False)

    files = {"file": ("image.jpg", b"\xff\xd8\xff", "image/jpeg")}
    resp = await client.post(f"/api/v1/recipes/{r.id}/image", files=files, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 500
    assert "Failed to save image" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_favorite_and_unfavorite_branches(client, db_session):
    u = User(username="favuser", email="fav@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r = Recipe(title="FavR", owner_id=u.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    token = create_access_token({"sub": str(u.id)})

    # add favorite
    resp = await client.post(f"/api/v1/recipes/{r.id}/favorite", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201

    # adding again -> 400
    resp2 = await client.post(f"/api/v1/recipes/{r.id}/favorite", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 400

    # unfavorite
    resp3 = await client.delete(f"/api/v1/recipes/{r.id}/favorite", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 204

    # unfavorite again -> 404
    resp4 = await client.delete(f"/api/v1/recipes/{r.id}/favorite", headers={"Authorization": f"Bearer {token}"})
    assert resp4.status_code == 404


@pytest.mark.asyncio
async def test_ratings_create_and_update_and_delete(client, db_session):
    u = User(username="ruser", email="r@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r = Recipe(title="RateR", owner_id=u.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    token = create_access_token({"sub": str(u.id)})

    # create rating
    resp = await client.post(f"/api/v1/recipes/{r.id}/ratings", json={"rating": 4, "review": "ok"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["rating"] == 4

    # create again updates existing rating (endpoint returns 201 even for update)
    resp2 = await client.post(f"/api/v1/recipes/{r.id}/ratings", json={"rating": 5, "review": "better"}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 201
    assert resp2.json()["rating"] == 5

    # delete rating
    resp3 = await client.delete(f"/api/v1/recipes/{r.id}/ratings", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 204

    # delete again -> 404
    resp4 = await client.delete(f"/api/v1/recipes/{r.id}/ratings", headers={"Authorization": f"Bearer {token}"})
    assert resp4.status_code == 404


@pytest.mark.asyncio
async def test_export_and_import_recipes_success_and_errors(client, db_session, tmp_path):
    u = User(username="exuser", email="ex@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r = Recipe(title="ExR", owner_id=u.id, ingredients=[{"name": "foo", "quantity": 1}], instructions=["do"], serving_size=2)
    db_session.add(r)
    await db_session.commit()

    token = create_access_token({"sub": str(u.id)})

    resp = await client.get("/api/v1/recipes/export/all", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "recipes_" in resp.headers.get("Content-Disposition", "")
    body = json.loads(resp.text)
    assert isinstance(body, list)
    assert any(item["title"] == "ExR" for item in body)

    # import invalid json
    files = {"file": ("bad.json", b"notjson", "application/json")}
    resp2 = await client.post("/api/v1/recipes/import", files=files, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 400

    # import with missing fields
    bad = [{"title": "NoIng"}, {"ingredients": []}]
    files2 = {"file": ("recipes.json", json.dumps(bad).encode(), "application/json")}
    resp3 = await client.post("/api/v1/recipes/import", files=files2, headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 200
    data = resp3.json()
    assert data["imported"] == 0
    assert data["errors"] is not None
