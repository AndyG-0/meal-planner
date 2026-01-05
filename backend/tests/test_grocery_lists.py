from types import SimpleNamespace

import pytest


@pytest.mark.asyncio
async def test_consolidate_ingredients():
    from app.api.v1.endpoints.grocery_lists import consolidate_ingredients

    r1 = SimpleNamespace(ingredients=[{"name": "Sugar", "quantity": 1, "unit": "cup"}])
    r2 = SimpleNamespace(ingredients=[{"name": "sugar", "quantity": 2, "unit": "cup"}, {"name": "Flour", "quantity": 1, "unit": "cup"}])

    out = consolidate_ingredients([r1, r2])
    # sugar should be consolidated to 3 cups
    sugar = next((i for i in out if i["name"] == "sugar"), None)
    assert sugar is not None
    assert float(sugar["quantity"]) == pytest.approx(3.0)


@pytest.mark.asyncio
async def test_create_grocery_list_and_export(client, db_session, test_user, test_token):
    from datetime import datetime

    from app.models import Calendar, CalendarMeal, Recipe

    # Create a recipe with ingredients
    r = Recipe(title="R1", owner_id=test_user.id, ingredients=[{"name": "Tomato", "quantity": 2, "unit": "pcs"}], instructions=["a"], prep_time=1, cook_time=1, serving_size=1)
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # Create calendar and add a meal
    cal = Calendar(name="C1", owner_id=test_user.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    m = CalendarMeal(calendar_id=cal.id, recipe_id=r.id, meal_date=datetime.utcnow(), meal_type="dinner")
    db_session.add(m)
    await db_session.commit()

    # Create grocery list via endpoint
    payload = {"name": "My List"}
    resp = await client.post(f"/api/v1/grocery-lists?calendar_id={cal.id}", json=payload, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My List"
    assert data["items"] and any(it["name"].lower() == "tomato" for it in data["items"])

    # Export CSV
    gl_id = data["id"]
    resp = await client.get(f"/api/v1/grocery-lists/{gl_id}/export/csv", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert resp.headers.get("Content-Disposition")

    # Export TXT
    resp = await client.get(f"/api/v1/grocery-lists/{gl_id}/export/txt", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert resp.headers.get("Content-Disposition")

    # Print (HTML)
    resp = await client.get(f"/api/v1/grocery-lists/{gl_id}/print", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert "<html>" in resp.text


@pytest.mark.asyncio
async def test_create_grocery_list_permission_denied(client, db_session, test_user, test_token):
    from app.models import Calendar

    other = SimpleNamespace(id=9999)

    cal = Calendar(name="OtherCal", owner_id=other.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    payload = {"name": "X"}
    resp = await client.post(f"/api/v1/grocery-lists?calendar_id={cal.id}", json=payload, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 403
