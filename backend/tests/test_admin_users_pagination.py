import pytest

from app.models import User
from app.utils.auth import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_admin_users_pagination(client, db_session):
    # create admin
    admin = User(username="upadmin", email="ua@example.com", password_hash=get_password_hash("p"), is_admin=True)
    db_session.add(admin)

    # create many users
    users = [User(username=f"u{i}", email=f"u{i}@example.com", password_hash=get_password_hash("p")) for i in range(10)]
    db_session.add_all(users)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    # default list should return up to limit
    resp = await client.get("/api/v1/admin/users?skip=0&limit=5", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 5

    # pagination next page
    resp2 = await client.get("/api/v1/admin/users?skip=5&limit=5", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_admin_user_promote_and_email_conflict(client, db_session):
    admin = User(username="promadmin", email="pa@example.com", password_hash=get_password_hash("p"), is_admin=True)
    u1 = User(username="usera", email="a@example.com", password_hash=get_password_hash("p"))
    u2 = User(username="userb", email="b@example.com", password_hash=get_password_hash("p"))
    db_session.add_all([admin, u1, u2])
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    # Promote u1 to admin
    resp = await client.patch(f"/api/v1/admin/users/{u1.id}", json={"is_admin": True}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["is_admin"] is True

    # Email conflict when updating
    resp2 = await client.patch(f"/api/v1/admin/users/{u1.id}", json={"email": u2.email}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 400
