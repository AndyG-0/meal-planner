import pytest
from app.models import User, Group, GroupMember
from app.utils.auth import create_access_token


@pytest.mark.asyncio
async def test_get_user_groups_combines_owned_and_member(client, db_session, test_user, test_token):
    owner = test_user
    # create owned group
    g1 = Group(name="OwnedG", owner_id=owner.id)
    db_session.add(g1)

    # create group owned by other, add test_user as member
    other = User(username="gg", email="gg@example.com", password_hash="x")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    g2 = Group(name="MemberG", owner_id=other.id)
    db_session.add(g2)
    await db_session.commit()
    await db_session.refresh(g2)

    gm = GroupMember(group_id=g2.id, user_id=owner.id, role="member")
    db_session.add(gm)
    await db_session.commit()

    resp = await client.get("/api/v1/groups", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    data = resp.json()
    names = [g["name"] for g in data]
    assert "OwnedG" in names
    assert "MemberG" in names


@pytest.mark.asyncio
async def test_update_and_delete_group_permissions(client, db_session, test_user, test_token):
    owner = test_user
    g = Group(name="UpdG", owner_id=owner.id)
    db_session.add(g)
    await db_session.commit()
    await db_session.refresh(g)

    # other cannot update
    other = User(username="o3", email="o3@example.com", password_hash="x")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)
    other_token = create_access_token({"sub": str(other.id)})

    resp = await client.patch(f"/api/v1/groups/{g.id}", json={"name": "X"}, headers={"Authorization": f"Bearer {other_token}"})
    assert resp.status_code == 403

    # owner can update
    resp2 = await client.patch(f"/api/v1/groups/{g.id}", json={"name": "X"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 200
    assert resp2.json()["name"] == "X"

    # non-owner cannot delete
    resp3 = await client.delete(f"/api/v1/groups/{g.id}", headers={"Authorization": f"Bearer {other_token}"})
    assert resp3.status_code == 403

    # owner can delete
    resp4 = await client.delete(f"/api/v1/groups/{g.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp4.status_code == 204