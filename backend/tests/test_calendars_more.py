import pytest
from datetime import datetime, timedelta
from app.utils.auth import create_access_token
from app.models import User, Calendar, CalendarMeal, Recipe


@pytest.mark.asyncio
async def test_calendar_crud_and_meals(client, db_session, test_user, test_token):
    # create calendar
    resp = await client.post("/api/v1/calendars", json={"name": "MyCal"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    cal = resp.json()

    cal_id = cal["id"] if isinstance(cal, dict) and "id" in cal else cal.get("id")

    # create recipe
    r = Recipe(title="MealRecipe", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # add meal
    meal_date = datetime.utcnow().isoformat()
    resp2 = await client.post(f"/api/v1/calendars/{cal_id}/meals", json={"recipe_id": r.id, "meal_date": meal_date, "meal_type": "dinner"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 201
    meal = resp2.json()
    assert meal["recipe_id"] == r.id

    # list meals
    resp3 = await client.get(f"/api/v1/calendars/{cal_id}/meals", headers={"Authorization": f"Bearer {test_token}"})
    assert resp3.status_code == 200
    assert any(m["recipe_id"] == r.id for m in resp3.json())

    # export ical
    resp4 = await client.get(f"/api/v1/calendars/{cal_id}/export/ical", headers={"Authorization": f"Bearer {test_token}"})
    assert resp4.status_code == 200
    assert "BEGIN:VCALENDAR" in resp4.text

    # remove meal
    meal_id = meal["id"]
    resp5 = await client.delete(f"/api/v1/calendars/{cal_id}/meals/{meal_id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp5.status_code == 204

    # delete calendar
    resp6 = await client.delete(f"/api/v1/calendars/{cal_id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp6.status_code == 204


@pytest.mark.asyncio
async def test_copy_calendar_no_source_meals(client, db_session, test_user, test_token):
    # create calendar
    resp = await client.post("/api/v1/calendars", json={"name": "CopyCal"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    cal = resp.json()
    cal_id = cal["id"] if isinstance(cal, dict) and "id" in cal else cal.get("id")

    # attempt to copy a week where there are no meals
    src_date = datetime.utcnow().isoformat()
    tgt_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
    resp2 = await client.post(f"/api/v1/calendars/{cal_id}/copy", json={"source_date": src_date, "target_date": tgt_date, "period": "week", "overwrite": False}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 404
