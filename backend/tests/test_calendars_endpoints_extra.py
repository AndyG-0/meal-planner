import pytest
from datetime import datetime, timedelta
from app.utils.auth import get_password_hash, create_access_token
from app.models import User, Calendar, Recipe, CalendarMeal


@pytest.mark.asyncio
async def test_calendar_crud_and_meals(client, db_session, test_user, test_token):
    # Create calendar
    resp = await client.post("/api/v1/calendars", json={"name": "MyCal"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    cal = resp.json()

    # List calendars
    resp = await client.get("/api/v1/calendars", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert any(c["name"] == "MyCal" for c in resp.json())

    # Get calendar as owner
    cid = cal["id"]
    resp = await client.get(f"/api/v1/calendars/{cid}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200

    # Update calendar
    resp = await client.put(f"/api/v1/calendars/{cid}", json={"name": "MyCal2"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "MyCal2"

    # Add meal with missing recipe -> 404
    meal_date = datetime.utcnow().isoformat()
    resp = await client.post(f"/api/v1/calendars/{cid}/meals", json={"recipe_id": 9999, "meal_date": meal_date, "meal_type": "dinner"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 404

    # Create recipe and add meal
    r = Recipe(title="CalR", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    resp = await client.post(f"/api/v1/calendars/{cid}/meals", json={"recipe_id": r.id, "meal_date": meal_date, "meal_type": "dinner"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    m = resp.json()
    assert m["recipe_id"] == r.id

    # List meals
    resp = await client.get(f"/api/v1/calendars/{cid}/meals", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert any(meal["recipe_id"] == r.id for meal in resp.json())

    # Export iCal
    resp = await client.get(f"/api/v1/calendars/{cid}/export/ical", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert "BEGIN:VCALENDAR" in resp.text
    assert resp.headers["Content-Disposition"].endswith('.ics"') or resp.headers["Content-Disposition"].startswith("attachment;")

    # Delete meal
    meals = await db_session.execute(CalendarMeal.__table__.select().where(CalendarMeal.calendar_id == cid))
    meal_row = meals.first()
    if meal_row:
        mid = meal_row[0]
        resp = await client.delete(f"/api/v1/calendars/{cid}/meals/{mid}", headers={"Authorization": f"Bearer {test_token}"})
        assert resp.status_code == 204

    # Delete calendar
    resp = await client.delete(f"/api/v1/calendars/{cid}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_copy_calendar_no_source_meals(client, db_session, test_user, test_token):
    # create calendar
    resp = await client.post("/api/v1/calendars", json={"name": "CopyCal"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    cal = resp.json()
    cid = cal["id"]

    # Attempt to copy when no meals -> should 404
    payload = {"source_date": datetime.utcnow().isoformat(), "target_date": (datetime.utcnow() + timedelta(days=7)).isoformat(), "period": "week", "overwrite": False}
    resp = await client.post(f"/api/v1/calendars/{cid}/copy", json=payload, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_calendar_permissions(client, db_session):
    # create owner and calendar
    owner = User(username="calowner", email="co@example.com", password_hash=get_password_hash("p"))
    db_session.add(owner)
    await db_session.commit()
    await db_session.refresh(owner)

    cal = Calendar(name="OtherCal", owner_id=owner.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    # login as different user
    other = User(username="otheru", email="ou@example.com", password_hash=get_password_hash("p"))
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    token = create_access_token({"sub": str(other.id)})

    resp = await client.get(f"/api/v1/calendars/{cal.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403

    resp = await client.put(f"/api/v1/calendars/{cal.id}", json={"name": "X"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403

    resp = await client.delete(f"/api/v1/calendars/{cal.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403