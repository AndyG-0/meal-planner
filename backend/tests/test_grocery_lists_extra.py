import pytest
from datetime import datetime
from app.models import User, Calendar, CalendarMeal, Recipe, GroceryList
from app.utils.auth import get_password_hash


def test_consolidate_ingredients_simple():
    from app.api.v1.endpoints.grocery_lists import consolidate_ingredients

    class R:
        def __init__(self, ingredients):
            self.ingredients = ingredients

    r1 = R([{"name": "tomato", "quantity": 1, "unit": "cup"}])
    r2 = R([{"name": "tomato", "quantity": 2, "unit": "cup"}, {"name": "onion", "quantity": 1, "unit": "serving"}])
    items = consolidate_ingredients([r1, r2])
    assert any(i["name"] == "tomato" and i["quantity"] == 3 for i in items)


@pytest.mark.asyncio
async def test_create_list_and_exports(client, db_session, test_user, test_token):
    # create calendar and recipe and meal
    cal = Calendar(name="GLCal", owner_id=test_user.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    r = Recipe(title="GLR", owner_id=test_user.id, ingredients=[{"name": "tomato", "quantity": 2, "unit": "cup"}], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    meal = CalendarMeal(calendar_id=cal.id, recipe_id=r.id, meal_date=datetime.utcnow(), meal_type="dinner")
    db_session.add(meal)
    await db_session.commit()

    # Create grocery list from calendar
    resp = await client.post(f"/api/v1/grocery-lists?calendar_id={cal.id}", json={"name": "GL1"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    gl = resp.json()

    # Exports
    gid = gl["id"]
    resp_csv = await client.get(f"/api/v1/grocery-lists/{gid}/export/csv", headers={"Authorization": f"Bearer {test_token}"})
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]

    resp_txt = await client.get(f"/api/v1/grocery-lists/{gid}/export/txt", headers={"Authorization": f"Bearer {test_token}"})
    assert resp_txt.status_code == 200
    assert "Grocery List" in resp_txt.text

    resp_print = await client.get(f"/api/v1/grocery-lists/{gid}/print", headers={"Authorization": f"Bearer {test_token}"})
    assert resp_print.status_code == 200
    assert "<html" in resp_print.text.lower()


@pytest.mark.asyncio
async def test_create_list_calendar_not_found(client, test_user, test_token):
    resp = await client.post(f"/api/v1/grocery-lists?calendar_id=9999", json={"name": "GLX"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_grocery_list_permissions(client, db_session):
    user = User(username="glowner", email="glo@example.com", password_hash=get_password_hash("p"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    gl = GroceryList(user_id=user.id, name="OwnList", items=[{"name": "a", "quantity": 1, "unit": "cup"}])
    db_session.add(gl)
    await db_session.commit()
    await db_session.refresh(gl)

    # Other user token
    other = User(username="othergl", email="og@example.com", password_hash=get_password_hash("p"))
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    from app.utils.auth import create_access_token
    token = create_access_token({"sub": str(other.id)})

    resp = await client.get(f"/api/v1/grocery-lists/{gl.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403

    resp = await client.patch(f"/api/v1/grocery-lists/{gl.id}", json=[{"name": "a", "quantity": 1, "unit": "cup", "checked": True}], headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403

    resp = await client.delete(f"/api/v1/grocery-lists/{gl.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403