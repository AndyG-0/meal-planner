import pytest

from app.models import Recipe, User
from app.utils.auth import create_access_token


@pytest.mark.asyncio
async def test_clean_ingredient_parsing_in_get_and_list(client, db_session):
    u = User(username="cleanu", email="cleanu@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    # ingredient with measurement in name
    ing = [{"name": "(100 g) cheese"}, {"name": "1/2 cup flour"}, {"name": "salt", "quantity": 2}]
    r = Recipe(title="CleanR", owner_id=u.id, ingredients=ing, instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    token = create_access_token({"sub": str(u.id)})

    resp = await client.get(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["ingredients"], list)
    # check parsed fields present
    assert any(i.get("unit") is not None for i in data["ingredients"])


@pytest.mark.asyncio
async def test_calculate_nutrition_handles_none_and_fraction(client, db_session):
    u = User(username="nutu", email="nut@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    ing = [{"name": "egg", "quantity": None, "unit": "piece"}, {"name": "flour", "quantity": 0.5, "unit": "cup"}]
    r = Recipe(title="NutR", owner_id=u.id, ingredients=ing, serving_size=2, instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    resp = await client.get(f"/api/v1/recipes/{r.id}/nutrition")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # ensure keys like total calories are present
    assert "total" in data and "calories" in data["total"]
