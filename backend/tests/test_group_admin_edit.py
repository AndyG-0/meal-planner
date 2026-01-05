import pytest

from app.models import Group, GroupMember, Recipe, User
from app.utils.auth import get_password_hash


@pytest.mark.asyncio
async def test_group_admin_can_edit_group_recipe(client, db_session, test_user, test_token):
    # owner and group
    owner = User(username="groupowner3", email="go3@example.com", password_hash=get_password_hash("p"))
    db_session.add(owner)
    await db_session.commit()
    await db_session.refresh(owner)

    group = Group(name="G3", owner_id=owner.id)
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    r = Recipe(title="GR", owner_id=owner.id, visibility="group", group_id=group.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # add test_user as group admin
    gm = GroupMember(group_id=group.id, user_id=test_user.id, role="admin", permissions={})
    db_session.add(gm)
    await db_session.commit()

    # group admin can edit
    resp = await client.put(f"/api/v1/recipes/{r.id}", json={"title": "GR2"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "GR2"
