from datetime import datetime, timedelta

import pytest

from app.models import Calendar, CalendarMeal, Recipe
from app.utils.auth import create_access_token


@pytest.mark.asyncio
async def test_copy_calendar_overwrite_behavior(client, db_session, test_user, test_token):
    # create calendar
    cal = Calendar(name="CopySrc", owner_id=test_user.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    # create source meals for this week
    base_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    r1 = Recipe(title="SRC1", owner_id=test_user.id, category="dinner", visibility="public", ingredients=[], instructions=[])
    r2 = Recipe(title="SRC2", owner_id=test_user.id, category="dinner", visibility="public", ingredients=[], instructions=[])
    db_session.add_all([r1, r2])
    await db_session.commit()
    await db_session.refresh(r1)

    # create a meal on the source week
    source_start = base_date
    meal = CalendarMeal(calendar_id=cal.id, recipe_id=r1.id, meal_date=source_start, meal_type="dinner")
    db_session.add(meal)
    await db_session.commit()
    await db_session.refresh(meal)

    # Create existing target meal on target week to test skip
    target_start = base_date + timedelta(days=7)
    existing = CalendarMeal(calendar_id=cal.id, recipe_id=r2.id, meal_date=target_start, meal_type="dinner")
    db_session.add(existing)
    await db_session.commit()

    token = create_access_token({"sub": str(test_user.id)})

    # copy with overwrite=False -> should skip existing slot
    resp = await client.post(f"/api/v1/calendars/{cal.id}/copy", json={"source_date": source_start.isoformat(), "target_date": target_start.isoformat(), "period": "week", "overwrite": False}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["meals_copied"] == 0 or data["meals_skipped"] >= 1

    # copy with overwrite=True -> should delete existing and copy
    resp2 = await client.post(f"/api/v1/calendars/{cal.id}/copy", json={"source_date": source_start.isoformat(), "target_date": target_start.isoformat(), "period": "week", "overwrite": True}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["meals_copied"] >= 1
