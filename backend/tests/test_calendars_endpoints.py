"""Tests for calendar endpoints."""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Calendar, Recipe, User
from app.utils.auth import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_create_list_get_update_delete_calendar(
    client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession
):
    # Create
    resp = await client.post(
        "/api/v1/calendars",
        json={"name": "MyCal", "visibility": "private"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 201
    cal = resp.json()
    cal_id = cal["id"]

    # List
    resp = await client.get("/api/v1/calendars", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert any(c["id"] == cal_id for c in resp.json())

    # Get
    resp = await client.get(
        f"/api/v1/calendars/{cal_id}", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 200

    # Update
    resp = await client.put(
        f"/api/v1/calendars/{cal_id}",
        json={"name": "Renamed"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"

    # Unauthorized get by other user
    other = User(username="othercal", email="oc@example.com", password_hash=get_password_hash("p"))
    db_session.add(other)
    await db_session.commit()
    token_other = create_access_token({"sub": str(other.id)})

    resp = await client.get(
        f"/api/v1/calendars/{cal_id}", headers={"Authorization": f"Bearer {token_other}"}
    )
    assert resp.status_code == 403

    # Delete
    resp = await client.delete(
        f"/api/v1/calendars/{cal_id}", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_calendar_meals_and_export_copy(
    client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession
):
    # Create calendar and recipe
    cal = Calendar(name="MealCal", owner_id=test_user.id)
    db_session.add(cal)
    r = Recipe(
        title="MealRecipe",
        owner_id=test_user.id,
        category="dinner",
        visibility="public",
        ingredients=[],
        instructions=[],
    )
    db_session.add(r)
    await db_session.commit()

    # Add meal
    meal_date = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    resp = await client.post(
        f"/api/v1/calendars/{cal.id}/meals",
        json={"recipe_id": r.id, "meal_date": meal_date.isoformat(), "meal_type": "dinner"},
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 201
    meal = resp.json()
    meal_id = meal["id"]

    # List meals
    resp = await client.get(
        f"/api/v1/calendars/{cal.id}/meals", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 200
    assert any(m["id"] == meal_id for m in resp.json())

    # Export ical
    resp = await client.get(
        f"/api/v1/calendars/{cal.id}/export/ical", headers={"Authorization": f"Bearer {test_token}"}
    )
    assert resp.status_code == 200
    assert resp.text.startswith("BEGIN:VCALENDAR")

    # Copy period: attempt to copy week -> should succeed (source has one meal)
    source_date = meal_date
    target_date = meal_date + timedelta(days=7)

    resp = await client.post(
        f"/api/v1/calendars/{cal.id}/copy",
        json={
            "source_date": source_date.isoformat(),
            "target_date": target_date.isoformat(),
            "period": "week",
            "overwrite": False,
        },
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["meals_copied"] >= 1

    # Remove meal
    resp = await client.delete(
        f"/api/v1/calendars/{cal.id}/meals/{meal_id}",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 204

    # Copy when no source meals -> 404
    # Use a calendar with no meals
    cal2 = Calendar(name="EmptyCal", owner_id=test_user.id)
    db_session.add(cal2)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/calendars/{cal2.id}/copy",
        json={
            "source_date": source_date.isoformat(),
            "target_date": target_date.isoformat(),
            "period": "week",
            "overwrite": False,
        },
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert resp.status_code == 404
