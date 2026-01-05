import json

import pytest

from app.models import Recipe, User
from app.utils.auth import create_access_token


@pytest.mark.asyncio
async def test_create_recipe_and_pagination_metadata(client, db_session):
    u = User(username="createu", email="createu@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    token = create_access_token({"sub": str(u.id)})

    # create multiple recipes to force pagination
    for i in range(25):
        resp = await client.post("/api/v1/recipes", json={"title": f"R{i}", "ingredients": [], "instructions": []}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201

    # request with page_size 10 -> total_pages should be 3
    resp2 = await client.get("/api/v1/recipes?page=1&page_size=10", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["pagination"]["total_pages"] >= 3


@pytest.mark.asyncio
async def test_tag_add_remove_unauthorized(client, db_session):
    owner = User(username="towner", email="towner@example.com", password_hash="x")
    other = User(username="tother", email="tother@example.com", password_hash="x")
    db_session.add_all([owner, other])
    await db_session.commit()
    await db_session.refresh(owner)
    await db_session.refresh(other)

    r = Recipe(title="TagU", owner_id=owner.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    token_other = create_access_token({"sub": str(other.id)})
    # other cannot add tag -> 403
    resp = await client.post(f"/api/v1/recipes/{r.id}/tags", json={"tag_name": "x"}, headers={"Authorization": f"Bearer {token_other}"})
    assert resp.status_code == 403

    # owner adds tag
    token_owner = create_access_token({"sub": str(owner.id)})
    resp2 = await client.post(f"/api/v1/recipes/{r.id}/tags", json={"tag_name": "x"}, headers={"Authorization": f"Bearer {token_owner}"})
    assert resp2.status_code == 201
    tag_id = resp2.json()["id"]

    # other cannot remove
    resp3 = await client.delete(f"/api/v1/recipes/{r.id}/tags/{tag_id}", headers={"Authorization": f"Bearer {token_other}"})
    assert resp3.status_code == 403


@pytest.mark.asyncio
async def test_upload_image_unauthorized_and_import_success(client, db_session):
    owner = User(username="iu", email="iu@example.com", password_hash="x")
    other = User(username="io", email="io@example.com", password_hash="x")
    db_session.add_all([owner, other])
    await db_session.commit()
    await db_session.refresh(owner)
    await db_session.refresh(other)

    r = Recipe(title="ImgU", owner_id=owner.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()

    token_other = create_access_token({"sub": str(other.id)})
    files = {"file": ("image.jpg", b"\xff\xd8\xff", "image/jpeg")}
    resp = await client.post(f"/api/v1/recipes/{r.id}/image", files=files, headers={"Authorization": f"Bearer {token_other}"})
    assert resp.status_code == 403

    # import success with valid JSON
    token_owner = create_access_token({"sub": str(owner.id)})
    payload = [{"title": "Imp1", "ingredients": []}, {"title": "Imp2", "ingredients": []}]
    files2 = {"file": ("recipes.json", json.dumps(payload).encode(), "application/json")}
    resp2 = await client.post("/api/v1/recipes/import", files=files2, headers={"Authorization": f"Bearer {token_owner}"})
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["imported"] == 2


@pytest.mark.asyncio
async def test_rate_recipe_update_and_get_ratings(client, db_session):
    u = User(username="rateu", email="rateu@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r = Recipe(title="RateR2", owner_id=u.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    token = create_access_token({"sub": str(u.id)})

    # create rating
    resp = await client.post(f"/api/v1/recipes/{r.id}/ratings", json={"rating": 3, "review": "ok"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    assert resp.json()["rating"] == 3

    # update rating
    resp2 = await client.post(f"/api/v1/recipes/{r.id}/ratings", json={"rating": 5, "review": "great"}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code in (200, 201)
    assert resp2.json()["rating"] == 5

    # get ratings list
    resp3 = await client.get(f"/api/v1/recipes/{r.id}/ratings")
    assert resp3.status_code == 200
    assert isinstance(resp3.json(), list)
    assert any(x["rating"] == 5 for x in resp3.json())
