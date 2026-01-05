import json
import os
import io
import pytest
from httpx import AsyncClient
from app.utils.auth import create_access_token
from app.models import Recipe, RecipeTag, User, UserFavorite, RecipeRating


@pytest.mark.asyncio
async def test_create_recipe_returns_expected_fields(client: AsyncClient, test_user, test_token):
    payload = {
        "title": "Test Create",
        "ingredients": [],
        "instructions": [],
    }
    resp = await client.post("/api/v1/recipes", json=payload, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Create"
    assert data["is_favorite"] is False
    assert data["tags"] == []


@pytest.mark.asyncio
async def test_add_and_remove_tag_permissions(client: AsyncClient, db_session, test_user, test_token):
    # create recipe
    recipe = Recipe(title="TagR", owner_id=test_user.id, ingredients=[], instructions=[], visibility="private")
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)

    # add tag as owner
    resp = await client.post(f"/api/v1/recipes/{recipe.id}/tags", json={"tag_name": "sweet"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    tag_data = resp.json()
    assert tag_data["tag_name"] == "sweet"

    # adding same tag again should return 400
    resp2 = await client.post(f"/api/v1/recipes/{recipe.id}/tags", json={"tag_name": "sweet"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 400

    # remove tag as owner
    resp3 = await client.delete(f"/api/v1/recipes/{recipe.id}/tags/{tag_data['id']}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp3.status_code == 204

    # non-owner cannot add tag
    other = User(username="other", email="o@example.com", password_hash="x")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)
    other_token = create_access_token({"sub": str(other.id)})

    resp4 = await client.post(f"/api/v1/recipes/{recipe.id}/tags", json={"tag_name": "hot"}, headers={"Authorization": f"Bearer {other_token}"})
    assert resp4.status_code == 403


@pytest.mark.asyncio
async def test_favorite_and_unfavorite_flow(client: AsyncClient, db_session, test_user, test_token):
    recipe = Recipe(title="FavR", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)

    # favorite
    resp = await client.post(f"/api/v1/recipes/{recipe.id}/favorite", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201

    # favorite again -> 400
    resp2 = await client.post(f"/api/v1/recipes/{recipe.id}/favorite", headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 400

    # unfavorite
    resp3 = await client.delete(f"/api/v1/recipes/{recipe.id}/favorite", headers={"Authorization": f"Bearer {test_token}"})
    assert resp3.status_code == 204

    # unfavorite again -> 404
    resp4 = await client.delete(f"/api/v1/recipes/{recipe.id}/favorite", headers={"Authorization": f"Bearer {test_token}"})
    assert resp4.status_code == 404


@pytest.mark.asyncio
async def test_rate_update_and_delete(client: AsyncClient, db_session, test_user, test_token):
    recipe = Recipe(title="RateR", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)

    # create rating
    resp = await client.post(f"/api/v1/recipes/{recipe.id}/ratings", json={"rating": 4, "review": "Nice"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["rating"] == 4

    # update rating
    resp2 = await client.post(f"/api/v1/recipes/{recipe.id}/ratings", json={"rating": 5, "review": "Great"}, headers={"Authorization": f"Bearer {test_token}"})
    # endpoint always returns 201 (created) even when updating existing rating
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["rating"] == 5

    # get ratings
    resp3 = await client.get(f"/api/v1/recipes/{recipe.id}/ratings")
    assert resp3.status_code == 200
    assert any(r["rating"] == 5 for r in resp3.json())

    # delete rating
    resp4 = await client.delete(f"/api/v1/recipes/{recipe.id}/ratings", headers={"Authorization": f"Bearer {test_token}"})
    assert resp4.status_code == 204

    # delete again -> 404
    resp5 = await client.delete(f"/api/v1/recipes/{recipe.id}/ratings", headers={"Authorization": f"Bearer {test_token}"})
    assert resp5.status_code == 404


@pytest.mark.asyncio
async def test_upload_image_validation_and_success(client: AsyncClient, db_session, test_user, test_token, tmp_path):
    recipe = Recipe(title="ImgR", owner_id=test_user.id, ingredients=[], instructions=[], visibility="private")
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)

    # invalid content-type
    files = {"file": ("notimage.txt", io.BytesIO(b"hello"), "text/plain")}
    resp = await client.post(f"/api/v1/recipes/{recipe.id}/image", files=files, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 400

    # valid image
    files = {"file": ("image.jpg", io.BytesIO(b"\xff\xd8\xff"), "image/jpeg")}
    resp2 = await client.post(f"/api/v1/recipes/{recipe.id}/image", files=files, headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["image_url"] and "uploads/recipes" in data["image_url"]


@pytest.mark.asyncio
async def test_calculate_nutrition_and_export_import(client: AsyncClient, db_session, test_user, test_token):
    recipe = Recipe(
        title="NutR",
        owner_id=test_user.id,
        ingredients=[{"name": "100 g chicken breast", "quantity": None, "unit": ""}],
        instructions=[],
        serving_size=2,
        visibility="private",
    )
    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)

    # nutrition
    resp = await client.get(f"/api/v1/recipes/{recipe.id}/nutrition")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data and "per_serving" in data

    # export
    resp2 = await client.get("/api/v1/recipes/export/all", headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 200
    assert "Content-Disposition" in resp2.headers

    # import invalid JSON
    files = {"file": ("data.json", io.BytesIO(b"{notjson}"), "application/json")}
    resp3 = await client.post("/api/v1/recipes/import", files=files, headers={"Authorization": f"Bearer {test_token}"})
    assert resp3.status_code == 400

    # import non-list JSON
    files = {"file": ("data.json", io.BytesIO(b"{}"), "application/json")}
    resp4 = await client.post("/api/v1/recipes/import", files=files, headers={"Authorization": f"Bearer {test_token}"})
    assert resp4.status_code == 400

    # import valid list
    payload = [{"title": "I1", "ingredients": [], "instructions": []}, {"title": "I2", "ingredients": [], "instructions": []}]
    files = {"file": ("data.json", io.BytesIO(json.dumps(payload).encode()), "application/json")}
    resp5 = await client.post("/api/v1/recipes/import", files=files, headers={"Authorization": f"Bearer {test_token}"})
    assert resp5.status_code == 200
    data5 = resp5.json()
    assert data5["imported"] == 2
