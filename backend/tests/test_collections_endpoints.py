"""Tests for recipe collection endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Recipe, RecipeCollection, RecipeCollectionItem


@pytest.mark.asyncio
async def test_collection_crud_and_recipe_management(client: AsyncClient, test_user, test_token, db_session: AsyncSession):
    # Create a collection
    resp = await client.post("/api/v1/collections", json={"name": "C1", "description": "desc"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    coll = resp.json()
    cid = coll["id"]

    # Get collection
    resp = await client.get(f"/api/v1/collections/{cid}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200

    # Create a recipe
    r = Recipe(title="RC1", owner_id=test_user.id, category="dinner", visibility="public", ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()

    # Add recipe to collection
    resp = await client.post(f"/api/v1/collections/{cid}/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201

    # Duplicate add should fail
    resp = await client.post(f"/api/v1/collections/{cid}/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 400

    # Get recipes in collection
    resp = await client.get(f"/api/v1/collections/{cid}/recipes", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert any(rr["title"] == "RC1" for rr in resp.json())

    # Remove recipe
    resp = await client.delete(f"/api/v1/collections/{cid}/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 204

    # Delete collection
    resp = await client.delete(f"/api/v1/collections/{cid}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 204
