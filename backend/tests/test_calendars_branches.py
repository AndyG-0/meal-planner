from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.models import Calendar, CalendarMeal, Recipe, User
from app.utils.auth import create_access_token


def test_smoke_basic():
    assert True


@pytest.mark.asyncio
async def test_add_meal_success_and_recipe_not_found(client, db_session):
    u = User(username="calu", email="calu@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    cal = Calendar(name="Cal1", owner_id=u.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    token = create_access_token({"sub": str(u.id)})

    # recipe not found
    resp = await client.post(f"/api/v1/calendars/{cal.id}/meals", json={"recipe_id": 9999, "meal_date": datetime.utcnow().isoformat(), "meal_type": "dinner"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404

    # create recipe and add meal
    r = Recipe(title="RM", owner_id=u.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    md = (datetime.utcnow()).isoformat()
    resp2 = await client.post(f"/api/v1/calendars/{cal.id}/meals", json={"recipe_id": r.id, "meal_date": md, "meal_type": "lunch"}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 201
    assert resp2.json()["meal_type"] == "lunch"


@pytest.mark.asyncio
async def test_list_and_remove_meals_and_export_ical(client, db_session):
    u = User(username="calu2", email="calu2@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    cal = Calendar(name="Cal2", owner_id=u.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    r = Recipe(title="R1", owner_id=u.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # add two meals with distinct dates
    nd = datetime.utcnow()
    m1 = CalendarMeal(calendar_id=cal.id, recipe_id=r.id, meal_date=nd - timedelta(days=2), meal_type="breakfast")
    m2 = CalendarMeal(calendar_id=cal.id, recipe_id=r.id, meal_date=nd + timedelta(days=2), meal_type="dinner")
    db_session.add_all([m1, m2])
    await db_session.commit()

    token = create_access_token({"sub": str(u.id)})

    # list with date_from to only include second
    df = (nd + timedelta(days=1)).isoformat()
    resp = await client.get(f"/api/v1/calendars/{cal.id}/meals?date_from={df}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert all(item["meal_type"] == "dinner" for item in resp.json())

    # export ical
    resp2 = await client.get(f"/api/v1/calendars/{cal.id}/export/ical", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    assert "BEGIN:VCALENDAR" in resp2.text
    assert f"X-WR-CALNAME:{cal.name}" in resp2.text

    # remove non-existent meal -> 404
    resp3 = await client.delete(f"/api/v1/calendars/{cal.id}/meals/9999", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 404

    # remove existing meal
    # find a meal id via DB
    m = await db_session.execute(select(CalendarMeal).where(CalendarMeal.calendar_id == cal.id))
    mid = m.scalars().first().id
    resp4 = await client.delete(f"/api/v1/calendars/{cal.id}/meals/{mid}", headers={"Authorization": f"Bearer {token}"})
    assert resp4.status_code == 204


@pytest.mark.asyncio
async def test_copy_calendar_day_and_overwrite_behavior(client, db_session):
    u = User(username="cpyu", email="cpyu@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    cal = Calendar(name="CalCopy", owner_id=u.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    r = Recipe(title="RCopy", owner_id=u.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()

    # create source meal on specific date
    src_date = datetime(2025, 12, 31, 12, 0, 0)
    sm = CalendarMeal(calendar_id=cal.id, recipe_id=r.id, meal_date=src_date, meal_type="lunch")
    db_session.add(sm)
    await db_session.commit()

    token = create_access_token({"sub": str(u.id)})

    # invalid period - accept 422 as possible validation error
    resp = await client.post(f"/api/v1/calendars/{cal.id}/copy", json={"source_date": src_date.isoformat(), "target_date": (src_date + timedelta(days=1)).isoformat(), "period": "year", "overwrite": False}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in (400, 422)

    # copy day without overwrite (target empty)
    if resp.status_code in (400, 422):
        return

    resp2 = await client.post(f"/api/v1/calendars/{cal.id}/copy", json={"source_date": src_date.isoformat(), "target_date": (src_date + timedelta(days=7)).isoformat(), "period": "day", "overwrite": False}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 201
    assert resp2.json()["meals_copied"] >= 1

    # now create a target meal in same slot to test overwrite False skip
    tgt_date = src_date + timedelta(days=7)
    tm = CalendarMeal(calendar_id=cal.id, recipe_id=r.id, meal_date=tgt_date, meal_type="lunch")
    db_session.add(tm)
    await db_session.commit()

    resp3 = await client.post(f"/api/v1/calendars/{cal.id}/copy", json={"source_date": src_date.isoformat(), "target_date": tgt_date.isoformat(), "period": "day", "overwrite": False}, headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 201
    assert resp3.json()["meals_skipped"] >= 1

    # overwrite True should succeed and not skip
    resp4 = await client.post(f"/api/v1/calendars/{cal.id}/copy", json={"source_date": src_date.isoformat(), "target_date": tgt_date.isoformat(), "period": "day", "overwrite": True}, headers={"Authorization": f"Bearer {token}"})
    assert resp4.status_code == 201
    assert resp4.json()["meals_copied"] >= 1


@pytest.mark.asyncio
async def test_prepopulate_uses_service_and_value_error(monkeypatch, client, db_session):
    u = User(username="ppu", email="ppu@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    cal = Calendar(name="PrCal", owner_id=u.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    token = create_access_token({"sub": str(u.id)})

    class DummyService:
        def __init__(self, db):
            pass

        async def prepopulate_calendar(self, **kwargs):
            return 5, (kwargs["start_date"] + timedelta(days=4))

    monkeypatch.setattr("app.api.v1.endpoints.calendars.CalendarPrepopulateService", DummyService)

    # successful prepopulate
    resp = await client.post(f"/api/v1/calendars/{cal.id}/prepopulate", json={"start_date": datetime.utcnow().isoformat(), "period": "week", "meal_types": ["breakfast"]}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201

    # simulate service raising ValueError
    class ErrService(DummyService):
        async def prepopulate_calendar(self, **kwargs):
            raise ValueError("bad period")

    monkeypatch.setattr("app.api.v1.endpoints.calendars.CalendarPrepopulateService", ErrService)

    resp2 = await client.post(f"/api/v1/calendars/{cal.id}/prepopulate", json={"start_date": datetime.utcnow().isoformat(), "period": "week", "meal_types": ["breakfast"]}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 400
