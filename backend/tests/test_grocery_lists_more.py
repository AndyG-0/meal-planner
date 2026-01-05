import io
import pytest
from datetime import datetime, timedelta
from app.api.v1.endpoints.grocery_lists import consolidate_ingredients
from app.models import Recipe, Calendar, CalendarMeal


def test_consolidate_ingredients_basic():
    r1 = Recipe(title="A", ingredients=[{"name": "Apple", "quantity": 2, "unit": "pcs"}], instructions=[])
    r2 = Recipe(title="B", ingredients=[{"name": "apple", "quantity": 1, "unit": "pcs"}, {"name": "Flour", "quantity": 100, "unit": "g"}], instructions=[])
    out = consolidate_ingredients([r1, r2])
    names = {i['name'] for i in out}
    assert 'apple' in names
    assert any(i['unit'] == 'pcs' for i in out)


@pytest.mark.asyncio
async def test_create_list_and_exports(client, db_session, test_user, test_token):
    # Create calendar and recipe
    resp = await client.post("/api/v1/calendars", json={"name": "GLCal"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    cal = resp.json()
    cal_id = cal.get("id")

    r = Recipe(title="GFood", owner_id=test_user.id, ingredients=[{"name":"apple","quantity":2,"unit":"pcs"}], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # Add meal
    meal_date = datetime.utcnow()
    meal = CalendarMeal(calendar_id=cal_id, recipe_id=r.id, meal_date=meal_date, meal_type="dinner")
    db_session.add(meal)
    await db_session.commit()

    # create grocery list for period
    date_from = (datetime.utcnow() - timedelta(days=1)).isoformat()
    date_to = (datetime.utcnow() + timedelta(days=1)).isoformat()
    resp2 = await client.post(f"/api/v1/grocery-lists?calendar_id={cal_id}", json={"name":"List1","date_from":date_from,"date_to":date_to}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 201
    gl = resp2.json()
    list_id = gl["id"] if isinstance(gl, dict) and "id" in gl else gl.get("id")

    # export csv
    resp3 = await client.get(f"/api/v1/grocery-lists/{list_id}/export/csv", headers={"Authorization": f"Bearer {test_token}"})
    assert resp3.status_code == 200
    assert "Content-Disposition" in resp3.headers

    # export txt
    resp4 = await client.get(f"/api/v1/grocery-lists/{list_id}/export/txt", headers={"Authorization": f"Bearer {test_token}"})
    assert resp4.status_code == 200
    assert "Grocery List" in resp4.text

    # print view
    resp5 = await client.get(f"/api/v1/grocery-lists/{list_id}/print", headers={"Authorization": f"Bearer {test_token}"})
    assert resp5.status_code == 200
    assert "<html>" in resp5.text
