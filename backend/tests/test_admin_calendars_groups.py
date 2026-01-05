import pytest
from app.utils.auth import create_access_token
from app.models import User, Calendar, Group, GroupMember


@pytest.mark.asyncio
async def test_admin_list_and_manage_calendars(client, db_session):
    admin = User(username="cadm", email="cadm@example.com", password_hash="x", is_admin=True)
    u = User(username="u_cal", email="u_cal@example.com", password_hash="x")
    db_session.add_all([admin, u])
    await db_session.commit()
    await db_session.refresh(u)

    cal = Calendar(name="Ctest", owner_id=u.id, visibility="public")
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    token = create_access_token({"sub": str(admin.id)})

    resp = await client.get("/api/v1/admin/calendars", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(item["name"] == "Ctest" for item in resp.json())

    resp2 = await client.get(f"/api/v1/admin/calendars/{cal.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["meal_count"] == 0

    # patch calendar
    resp3 = await client.patch(f"/api/v1/admin/calendars/{cal.id}", json={"name": "Cnew", "visibility": "private"}, headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 200
    assert resp3.json()["name"] == "Cnew"

    # delete
    resp4 = await client.delete(f"/api/v1/admin/calendars/{cal.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp4.status_code == 204

    # get now 404
    resp5 = await client.get(f"/api/v1/admin/calendars/{cal.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp5.status_code == 404


@pytest.mark.asyncio
async def test_admin_group_management_and_remove_member(client, db_session):
    admin = User(username="gadm", email="gadm@example.com", password_hash="x", is_admin=True)
    owner = User(username="gowner", email="gowner@example.com", password_hash="x")
    member = User(username="gmember", email="gmember@example.com", password_hash="x")
    db_session.add_all([admin, owner, member])
    await db_session.commit()
    await db_session.refresh(owner)
    await db_session.refresh(member)

    grp = Group(name="Gtest", owner_id=owner.id)
    db_session.add(grp)
    await db_session.commit()
    await db_session.refresh(grp)

    gm = GroupMember(group_id=grp.id, user_id=member.id, role="member")
    db_session.add(gm)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    resp = await client.get("/api/v1/admin/groups", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(item["name"] == "Gtest" for item in resp.json())

    resp2 = await client.get(f"/api/v1/admin/groups/{grp.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    assert any(m["username"] == "gmember" for m in resp2.json()["members"]) 

    # remove member by id
    # find member id via response
    member_id = [m["id"] for m in resp2.json()["members"] if m["username"] == "gmember"][0]
    resp3 = await client.delete(f"/api/v1/admin/groups/{grp.id}/members/{member_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 204

    # patch group name
    resp4 = await client.patch(f"/api/v1/admin/groups/{grp.id}", json={"name": "Gnew"}, headers={"Authorization": f"Bearer {token}"})
    assert resp4.status_code == 200
    assert resp4.json()["name"] == "Gnew"

    # delete group
    resp5 = await client.delete(f"/api/v1/admin/groups/{grp.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp5.status_code == 204

    # get now 404
    resp6 = await client.get(f"/api/v1/admin/groups/{grp.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp6.status_code == 404