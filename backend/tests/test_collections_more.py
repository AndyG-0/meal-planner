import pytest

from app.models import Recipe


@pytest.mark.asyncio
async def test_collections_crud_and_items(client, db_session, test_user, test_token):
    # create recipe
    r = Recipe(title="CR1", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # create collection
    resp = await client.post("/api/v1/collections", json={"name": "C1", "description": "desc"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    coll = resp.json()
    cid = coll["id"] if isinstance(coll, dict) and "id" in coll else coll.get("id")

    # add recipe to collection
    resp2 = await client.post(f"/api/v1/collections/{cid}/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 201

    # adding again should 400
    resp3 = await client.post(f"/api/v1/collections/{cid}/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp3.status_code == 400

    # get collection recipes
    resp4 = await client.get(f"/api/v1/collections/{cid}/recipes", headers={"Authorization": f"Bearer {test_token}"})
    assert resp4.status_code == 200
    assert any(item["id"] == r.id or item.get("id") for item in resp4.json())

    # remove recipe
    resp5 = await client.delete(f"/api/v1/collections/{cid}/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp5.status_code == 204

    # remove again -> 404
    resp6 = await client.delete(f"/api/v1/collections/{cid}/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp6.status_code == 404


@pytest.mark.asyncio
async def test_collection_not_found(client, test_token):
    resp = await client.get("/api/v1/collections/9999", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 404
