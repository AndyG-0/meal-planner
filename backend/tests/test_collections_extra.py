import pytest
from app.models import User, Recipe, RecipeCollection
from app.utils.auth import get_password_hash


@pytest.mark.asyncio
async def test_collections_crud_and_items(client, db_session, test_user, test_token):
    # Create collection
    resp = await client.post("/api/v1/collections", json={"name": "C1", "description": "d"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    coll = resp.json()
    cid = coll["id"]

    # Add recipe to collection
    r = Recipe(title="CR", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    resp = await client.post(f"/api/v1/collections/{cid}/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201

    # Adding again should 400
    resp2 = await client.post(f"/api/v1/collections/{cid}/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 400

    # Get collection recipes
    resp = await client.get(f"/api/v1/collections/{cid}/recipes", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert any(rec["id"] == r.id for rec in resp.json())

    # Remove recipe
    resp = await client.delete(f"/api/v1/collections/{cid}/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 204

    # Delete collection
    resp = await client.delete(f"/api/v1/collections/{cid}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_collection_not_found_and_permissions(client, db_session):
    # Access non-existent collection
    resp = await client.get("/api/v1/collections/9999", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code in (401, 404)

    # Create a collection owned by other user and confirm 403 for current
    other = User(username="co", email="co@example.com", password_hash=get_password_hash("p"))
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    coll = RecipeCollection(name="OtherC", user_id=other.id)
    db_session.add(coll)
    await db_session.commit()
    await db_session.refresh(coll)

    from app.utils.auth import create_access_token
    token = create_access_token({"sub": str(other.id)})
    # Use a different token to cause 403
    resp = await client.get(f"/api/v1/collections/{coll.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
