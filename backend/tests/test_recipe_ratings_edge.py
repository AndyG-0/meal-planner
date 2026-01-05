import pytest


@pytest.mark.asyncio
async def test_delete_nonexistent_rating(client, test_user, test_token):
    # Try deleting rating when none exists
    resp = await client.delete(f"/api/v1/recipes/99999/ratings", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_rating_update_and_conflict(client, test_user, test_token, db_session):
    from app.models import Recipe, RecipeRating

    r = Recipe(title="RateX", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # Create rating
    resp = await client.post(f"/api/v1/recipes/{r.id}/ratings", json={"rating": 5, "review": "Nice"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201

    # Update rating
    resp2 = await client.post(f"/api/v1/recipes/{r.id}/ratings", json={"rating": 3, "review": "Ok"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 201
    assert resp2.json()["rating"] == 3
