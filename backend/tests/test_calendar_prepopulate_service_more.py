from datetime import datetime, timedelta

import pytest

from app.models import Calendar, Recipe, RecipeTag, User
from app.services.calendar_prepopulate import CalendarPrepopulateService


@pytest.mark.asyncio
async def test_prepopulate_day_and_snack_and_dessert(db_session):
    # create user and calendar
    user = User(username="pcu", email="pcu@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    cal = Calendar(name="PCal", owner_id=user.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    # create recipes for breakfast and snack and dessert
    r_b = Recipe(title="B1", owner_id=user.id, category="breakfast", visibility="public", ingredients=[], instructions=[])
    r_s = Recipe(title="S1", owner_id=user.id, category="snack", visibility="public", ingredients=[], instructions=[])
    r_d = Recipe(title="D1", owner_id=user.id, category="dessert", visibility="public", ingredients=[], instructions=[])
    db_session.add_all([r_b, r_s, r_d])
    await db_session.commit()

    service = CalendarPrepopulateService(db_session)

    start = datetime.utcnow()
    meals_created, end_date = await service.prepopulate_calendar(
        calendar_id=cal.id,
        user=user,
        start_date=start,
        period="day",
        meal_types=["breakfast"],
        snacks_per_day=1,
        desserts_per_day=1,
        use_dietary_preferences=False,
        avoid_duplicates=True,
    )

    # for a single day with 1 breakfast + 1 snack + 1 dessert -> meals_created == 3
    assert meals_created == 3
    assert end_date == start


@pytest.mark.asyncio
async def test_prepopulate_week_with_dietary_filter(db_session):
    # user with dietary preference
    user = User(username="dietu", email="diet@example.com", password_hash="x", dietary_preferences=["vegan"])
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    cal = Calendar(name="DietCal", owner_id=user.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    # create vegan dinner recipe and another non-vegan
    r1 = Recipe(title="VegDinner", owner_id=user.id, category="dinner", visibility="public", ingredients=[], instructions=[])
    r2 = Recipe(title="MeatDinner", owner_id=user.id, category="dinner", visibility="public", ingredients=[], instructions=[])
    db_session.add_all([r1, r2])
    await db_session.commit()
    await db_session.refresh(r1)
    await db_session.refresh(r2)

    # tag r1 as vegan
    rt = RecipeTag(recipe_id=r1.id, tag_name="vegan")
    db_session.add(rt)
    await db_session.commit()

    service = CalendarPrepopulateService(db_session)

    start = datetime.utcnow()
    meals_created, end_date = await service.prepopulate_calendar(
        calendar_id=cal.id,
        user=user,
        start_date=start,
        period="week",
        meal_types=["dinner"],
        use_dietary_preferences=True,
        avoid_duplicates=False,
    )

    # week (7 days) * 1 dinner = 7 meals
    assert meals_created == 7
    assert end_date == start + timedelta(days=6)


@pytest.mark.asyncio
async def test_prepopulate_raises_when_no_recipes(db_session):
    user = User(username="emptyu", email="empty@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    cal = Calendar(name="EmptyCal", owner_id=user.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    service = CalendarPrepopulateService(db_session)

    start = datetime.utcnow()

    with pytest.raises(ValueError):
        await service.prepopulate_calendar(
            calendar_id=cal.id,
            user=user,
            start_date=start,
            period="week",
            meal_types=["dinner"],
            use_dietary_preferences=False,
            avoid_duplicates=True,
        )
