"""Tests for grocery list endpoints."""

from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Calendar, CalendarMeal, GroceryList, Recipe, User
from app.utils.auth import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_create_and_export_grocery_list(client: AsyncClient, test_user, test_token, db_session: AsyncSession):
    # Setup calendar and recipes and meals
    cal = Calendar(name="GLCal", owner_id=test_user.id)
    r1 = Recipe(title="R1", owner_id=test_user.id, category="dinner", visibility="public", ingredients=[{"name":"tomato","quantity":2,"unit":"pcs"}], instructions=[])
    r2 = Recipe(title="R2", owner_id=test_user.id, category="dinner", visibility="public", ingredients=[{"name":"tomato","quantity":1,"unit":"pcs"},{"name":"salt","quantity":1,"unit":"tsp"}], instructions=[])
    db_session.add_all([cal, r1, r2])
    await db_session.commit()

    meal_date = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    m1 = CalendarMeal(calendar_id=cal.id, recipe_id=r1.id, meal_date=meal_date, meal_type="dinner")
    m2 = CalendarMeal(calendar_id=cal.id, recipe_id=r2.id, meal_date=meal_date, meal_type="dinner")
    db_session.add_all([m1, m2])
    await db_session.commit()

    # Create grocery list for the date
    resp = await client.post(f"/api/v1/grocery-lists?calendar_id={cal.id}", json={"name": "MyList", "date_from": meal_date.isoformat(), "date_to": meal_date.isoformat()}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    gl = resp.json()
    assert gl["name"] == "MyList"
    assert any(item["name"] == "tomato" for item in gl["items"])  # consolidated

    # Export CSV
    resp = await client.get(f"/api/v1/grocery-lists/{gl['id']}/export/csv", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]

    # Export TXT
    resp = await client.get(f"/api/v1/grocery-lists/{gl['id']}/export/txt", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]

    # Print HTML
    resp = await client.get(f"/api/v1/grocery-lists/{gl['id']}/print", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert "<html>" in resp.text

    # Update items
    new_items = [{"name": "tomato", "quantity": 5, "unit": "pcs", "checked": True}]
    resp = await client.patch(f"/api/v1/grocery-lists/{gl['id']}", json=new_items, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert resp.json()["items"][0]["checked"] is True

    # Delete
    resp = await client.delete(f"/api/v1/grocery-lists/{gl['id']}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_grocery_list_access_control(client: AsyncClient, test_user, test_token, db_session: AsyncSession):
    other = User(username="otherg", email="og@example.com", password_hash=get_password_hash("p"))
    db_session.add(other)
    await db_session.commit()
    token_other = create_access_token({"sub": str(other.id)})

    gl = GroceryList(user_id=test_user.id, name="Secret", items=[{"name":"a","quantity":1,"unit":"pcs"}])
    db_session.add(gl)
    await db_session.commit()

    # Other cannot access
    resp = await client.get(f"/api/v1/grocery-lists/{gl.id}", headers={"Authorization": f"Bearer {token_other}"})
    assert resp.status_code == 403
