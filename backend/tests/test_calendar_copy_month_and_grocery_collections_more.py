from datetime import datetime, timedelta

import pytest

from app.models import Calendar, CalendarMeal, Recipe, User
from app.utils.auth import create_access_token


@pytest.mark.asyncio
async def test_copy_calendar_month_and_overwrite(client, db_session, test_user, test_token):
    cal = Calendar(name="MonthC", owner_id=test_user.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    # create a source meal 15 days from now
    base = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    r = Recipe(title="M1", owner_id=test_user.id, category="dinner", visibility="public", ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    src_date = base
    meal = CalendarMeal(calendar_id=cal.id, recipe_id=r.id, meal_date=src_date, meal_type="dinner")
    db_session.add(meal)
    await db_session.commit()

    token = create_access_token({"sub": str(test_user.id)})

    # copy month
    resp = await client.post(f"/api/v1/calendars/{cal.id}/copy", json={"source_date": src_date.isoformat(), "target_date": (src_date + timedelta(days=30)).isoformat(), "period": "month", "overwrite": False}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["meals_copied"] >= 1


@pytest.mark.asyncio
async def test_grocery_list_permissions_and_update(client, db_session, test_user, test_token):
    cal = Calendar(name="GLC", owner_id=test_user.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    r = Recipe(title="Gr1", owner_id=test_user.id, ingredients=[{"name":"apple","quantity":2,"unit":"pcs"}], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # add meal
    meal = CalendarMeal(calendar_id=cal.id, recipe_id=r.id, meal_date=datetime.utcnow(), meal_type="dinner")
    db_session.add(meal)
    await db_session.commit()

    # create grocery list
    date_from = (datetime.utcnow() - timedelta(days=1)).isoformat()
    date_to = (datetime.utcnow() + timedelta(days=1)).isoformat()
    resp = await client.post(f"/api/v1/grocery-lists?calendar_id={cal.id}", json={"name":"GL1","date_from":date_from,"date_to":date_to}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    gl = resp.json()
    gid = gl["id"] if isinstance(gl, dict) and "id" in gl else gl.get("id")

    # other user cannot access
    other = User(username="nogl", email="nogl@example.com", password_hash="x")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)
    other_token = create_access_token({"sub": str(other.id)})

    resp2 = await client.get(f"/api/v1/grocery-lists/{gid}", headers={"Authorization": f"Bearer {other_token}"})
    assert resp2.status_code == 403

    # owner can update items
    items = [{"name": "apple", "quantity": 3, "unit": "pcs", "checked": True}]
    resp3 = await client.patch(f"/api/v1/grocery-lists/{gid}", json=items, headers={"Authorization": f"Bearer {test_token}"})
    assert resp3.status_code == 200
    assert any(item["name"] == "apple" for item in resp3.json()["items"])
