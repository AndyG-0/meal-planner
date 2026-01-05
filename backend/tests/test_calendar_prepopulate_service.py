"""Unit tests for CalendarPrepopulateService."""

from datetime import datetime

import pytest

from app.models import Calendar, Recipe, User
from app.services.calendar_prepopulate import CalendarPrepopulateService
from app.utils.auth import get_password_hash


@pytest.mark.asyncio
async def test_prepopulate_invalid_period(db_session):
    user = User(username="u1", email="u1@example.com", password_hash=get_password_hash("password"))
    db_session.add(user)
    await db_session.commit()

    service = CalendarPrepopulateService(db_session)

    with pytest.raises(ValueError):
        await service.prepopulate_calendar(1, user, datetime.now(), "invalid", ["breakfast"])


@pytest.mark.asyncio
async def test_prepopulate_success_week(db_session):
    # Create user and calendar
    user = User(username="u2", email="u2@example.com", password_hash=get_password_hash("password"))
    db_session.add(user)
    await db_session.commit()

    calendar = Calendar(name="Cal", owner_id=user.id)
    db_session.add(calendar)
    await db_session.commit()

    # Create recipes for each meal type as public
    recipes = []
    for cat in ["breakfast", "lunch", "dinner"]:
        r = Recipe(
            title=f"{cat}",
            owner_id=user.id,
            category=cat,
            visibility="public",
            ingredients=[{"name": "i", "quantity": 1, "unit": "u"}],
            instructions=["a"],
        )
        recipes.append(r)
        db_session.add(r)
    await db_session.commit()

    service = CalendarPrepopulateService(db_session)
    start = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)

    meals_created, end_date = await service.prepopulate_calendar(
        calendar.id,
        user,
        start,
        "week",
        ["breakfast", "lunch", "dinner"],
        snacks_per_day=0,
        desserts_per_day=0,
        use_dietary_preferences=False,
        avoid_duplicates=True,
    )

    # 7 days * 3 meals = 21
    assert meals_created == 21
    assert end_date >= start
