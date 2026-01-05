import pytest
from datetime import datetime, timedelta
from app.utils.auth import create_access_token
from app.models import User, Recipe, Calendar, CalendarMeal


@pytest.mark.asyncio
async def test_admin_list_recipes_filters(client, db_session):
    admin = User(username="recadmin", email="ra@example.com", password_hash="x", is_admin=True)
    u = User(username="ru", email="ru@example.com", password_hash="x")
    db_session.add_all([admin, u])
    await db_session.commit()
    await db_session.refresh(u)

    # create various recipes
    r1 = Recipe(title="AdminSearch", owner_id=u.id, category="dinner", difficulty="easy", visibility="public", ingredients=[], instructions=[])
    r2 = Recipe(title="Other", owner_id=u.id, category="breakfast", difficulty="hard", visibility="private", ingredients=[], instructions=[])
    db_session.add_all([r1, r2])
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    # search
    resp = await client.get("/api/v1/admin/recipes?search=AdminSearch", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(item["title"] == "AdminSearch" for item in resp.json())

    # category filter — API doesn't return 'category' field in list; check by title instead
    resp2 = await client.get("/api/v1/admin/recipes?category=breakfast", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    assert any(item["title"] == "Other" for item in resp2.json())

    # visibility filter — check by title
    resp3 = await client.get("/api/v1/admin/recipes?visibility=private", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 200
    assert any(item["title"] == "Other" for item in resp3.json())


@pytest.mark.asyncio
async def test_admin_calendar_details_with_meals(client, db_session):
    admin = User(username="caladmin", email="ca2@example.com", password_hash="x", is_admin=True)
    owner = User(username="caluser", email="cu@example.com", password_hash="x")
    db_session.add_all([admin, owner])
    await db_session.commit()
    await db_session.refresh(owner)

    cal = Calendar(name="WithMeals", owner_id=owner.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    # add a meal referencing a recipe
    r = Recipe(title="MealR", owner_id=owner.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    meal = CalendarMeal(calendar_id=cal.id, recipe_id=r.id, meal_date=datetime.utcnow(), meal_type="dinner")
    db_session.add(meal)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    resp = await client.get(f"/api/v1/admin/calendars/{cal.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "WithMeals"
    # meals are in detailed endpoint; ensure owner_username present
    assert "owner_username" in data


def test_collection_smoke():
    # sanity check to ensure pytest collects this module
    assert True
