import pytest
from app.utils.auth import create_access_token
from app.models import User, Recipe, Calendar, Group


@pytest.mark.asyncio
async def test_admin_user_list_counts(client, db_session):
    admin = User(username="admore", email="admore@example.com", password_hash="x", is_admin=True)
    u1 = User(username="count1", email="c1@example.com", password_hash="x")
    db_session.add_all([admin, u1])
    await db_session.commit()
    await db_session.refresh(u1)

    # add recipe, calendar, group for u1
    r = Recipe(title="RC", owner_id=u1.id, ingredients=[], instructions=[], visibility="public")
    c = Calendar(name="Cal1", owner_id=u1.id)
    g = Group(name="G1", owner_id=u1.id)
    db_session.add_all([r, c, g])
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})
    resp = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    users = resp.json()
    # find u1 in list
    found = next((u for u in users if u["username"] == "count1"), None)
    assert found is not None
    assert found["recipe_count"] >= 1
    assert found["calendar_count"] >= 1
    assert found["group_count"] >= 1


@pytest.mark.asyncio
async def test_get_and_delete_user_as_admin(client, db_session):
    admin = User(username="admore2", email="admore2@example.com", password_hash="x", is_admin=True)
    u = User(username="todel", email="td@example.com", password_hash="x")
    db_session.add_all([admin, u])
    await db_session.commit()
    await db_session.refresh(u)

    token = create_access_token({"sub": str(admin.id)})
    resp = await client.get(f"/api/v1/admin/users/{u.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    resp2 = await client.delete(f"/api/v1/admin/users/{u.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 204

    # get now should 404
    resp3 = await client.get(f"/api/v1/admin/users/{u.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_user_success(client, db_session):
    admin = User(username="admore3", email="admore3@example.com", password_hash="x", is_admin=True)
    u = User(username="up1", email="up1@example.com", password_hash="x")
    db_session.add_all([admin, u])
    await db_session.commit()
    await db_session.refresh(u)

    token = create_access_token({"sub": str(admin.id)})
    resp = await client.patch(f"/api/v1/admin/users/{u.id}", json={"email": "new@example.com", "is_admin": True}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["is_admin"] is True
