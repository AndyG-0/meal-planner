import pytest
from app.utils.auth import create_access_token, get_password_hash
from app.models import User, Group, GroupMember, Calendar


@pytest.mark.asyncio
async def test_admin_group_crud_and_member_deletion(client, db_session):
    admin = User(username="gadmin", email="ga@example.com", password_hash=get_password_hash("p"), is_admin=True)
    db_session.add(admin)

    owner = User(username="gowner", email="go@example.com", password_hash=get_password_hash("p"))
    db_session.add(owner)
    await db_session.commit()
    await db_session.refresh(owner)

    # create group by owner
    g = Group(name="AdminG", owner_id=owner.id)
    db_session.add(g)
    await db_session.commit()
    await db_session.refresh(g)

    token = create_access_token({"sub": str(admin.id)})

    # Admin list groups
    resp = await client.get("/api/v1/admin/groups", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(gr["name"] == "AdminG" for gr in resp.json())

    # Get group details
    resp = await client.get(f"/api/v1/admin/groups/{g.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # Patch group
    resp = await client.patch(f"/api/v1/admin/groups/{g.id}", json={"name": "AdminG2"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "AdminG2"

    # Add member then delete via admin
    gm = GroupMember(group_id=g.id, user_id=owner.id, role="admin", permissions={})
    db_session.add(gm)
    await db_session.commit()
    await db_session.refresh(gm)

    resp = await client.delete(f"/api/v1/admin/groups/{g.id}/members/{gm.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204

    # Delete group
    resp = await client.delete(f"/api/v1/admin/groups/{g.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_admin_calendar_crud(client, db_session):
    admin = User(username="cadmin", email="ca@example.com", password_hash=get_password_hash("p"), is_admin=True)
    owner = User(username="cowner", email="co@example.com", password_hash=get_password_hash("p"))
    db_session.add_all([admin, owner])
    await db_session.commit()
    await db_session.refresh(owner)

    cal = Calendar(name="C1", owner_id=owner.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    token = create_access_token({"sub": str(admin.id)})

    # List calendars
    resp = await client.get("/api/v1/admin/calendars", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(c["name"] == "C1" for c in resp.json())

    # Get details
    resp = await client.get(f"/api/v1/admin/calendars/{cal.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # Patch
    resp = await client.patch(f"/api/v1/admin/calendars/{cal.id}", json={"name": "C2"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "C2"

    # Delete
    resp = await client.delete(f"/api/v1/admin/calendars/{cal.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204
