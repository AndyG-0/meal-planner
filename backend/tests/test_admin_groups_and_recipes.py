import pytest
from app.utils.auth import create_access_token
from app.models import User, Group, GroupMember, Recipe


@pytest.mark.asyncio
async def test_group_details_and_admin_recipe_patch(client, db_session):
    admin = User(username="mgadmin", email="mg@example.com", password_hash="x", is_admin=True)
    owner = User(username="own", email="own@example.com", password_hash="x")
    db_session.add_all([admin, owner])
    await db_session.commit()

    g = Group(name="GG", owner_id=owner.id)
    db_session.add(g)
    await db_session.commit()
    await db_session.refresh(g)

    gm = GroupMember(group_id=g.id, user_id=owner.id, role="admin")
    db_session.add(gm)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    # get group details
    resp = await client.get(f"/api/v1/admin/groups/{g.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "GG"

    # admin can patch any recipe
    r = Recipe(title="PatchMe", owner_id=owner.id, ingredients=[], instructions=[], visibility="private")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    resp2 = await client.patch(f"/api/v1/admin/recipes/{r.id}", json={"title": "Patched"}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    assert resp2.json()["title"] == "Patched"
