import pytest
from app.utils.auth import create_access_token
from app.models import User, Group, GroupMember


@pytest.mark.asyncio
async def test_group_access_and_member_management(client, db_session, test_user, test_token):
    owner = test_user
    # create a group
    g = Group(name="GM", owner_id=owner.id)
    db_session.add(g)
    await db_session.commit()
    await db_session.refresh(g)

    # other user without membership cannot get group
    other = User(username="o", email="o@example.com", password_hash="x")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)
    other_token = create_access_token({"sub": str(other.id)})

    resp = await client.get(f"/api/v1/groups/{g.id}", headers={"Authorization": f"Bearer {other_token}"})
    assert resp.status_code == 403

    # owner can add member
    token_owner = create_access_token({"sub": str(owner.id)})
    resp2 = await client.post(f"/api/v1/groups/{g.id}/members", json={"user_id": other.id, "role": "member", "permissions": {}}, headers={"Authorization": f"Bearer {token_owner}"})
    assert resp2.status_code == 201

    # adding same member again -> 400
    resp3 = await client.post(f"/api/v1/groups/{g.id}/members", json={"user_id": other.id, "role": "member", "permissions": {}}, headers={"Authorization": f"Bearer {token_owner}"})
    assert resp3.status_code == 400

    # now other can access group
    resp4 = await client.get(f"/api/v1/groups/{g.id}", headers={"Authorization": f"Bearer {other_token}"})
    assert resp4.status_code == 200

    # owner can remove member
    members = (await client.get(f"/api/v1/groups/{g.id}/members", headers={"Authorization": f"Bearer {token_owner}"})).json()
    member_id = members[0]["id"]
    resp5 = await client.delete(f"/api/v1/groups/{g.id}/members/{member_id}", headers={"Authorization": f"Bearer {token_owner}"})
    assert resp5.status_code == 204

    # non-owner non-admin cannot add member
    nonadmin = User(username="na", email="na@example.com", password_hash="x")
    db_session.add(nonadmin)
    await db_session.commit()
    await db_session.refresh(nonadmin)
    na_token = create_access_token({"sub": str(nonadmin.id)})

    resp6 = await client.post(f"/api/v1/groups/{g.id}/members", json={"user_id": nonadmin.id, "role": "member", "permissions": {}}, headers={"Authorization": f"Bearer {na_token}"})
    assert resp6.status_code == 403
