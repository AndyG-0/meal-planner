import pytest
from sqlalchemy import select

from app.models import Group, GroupMember, Recipe, RecipeTag, User
from app.utils.auth import create_access_token


@pytest.mark.asyncio
async def test_get_recipe_group_access_and_forbidden(client, db_session):
    owner = User(username="owner", email="o@example.com", password_hash="x")
    other = User(username="other", email="other@example.com", password_hash="x")
    db_session.add_all([owner, other])
    await db_session.commit()
    await db_session.refresh(owner)
    await db_session.refresh(other)

    grp = Group(name="G", owner_id=owner.id)
    db_session.add(grp)
    await db_session.commit()
    await db_session.refresh(grp)

    # Create group recipe
    r = Recipe(title="GroupR", owner_id=owner.id, visibility="group", group_id=grp.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # other tries to access -> 403
    token_other = create_access_token({"sub": str(other.id)})
    resp = await client.get(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {token_other}"})
    assert resp.status_code == 403

    # add other as group member role admin
    gm = GroupMember(group_id=grp.id, user_id=other.id, role="admin")
    db_session.add(gm)
    await db_session.commit()

    # now can access
    resp2 = await client.get(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {token_other}"})
    assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_update_recipe_permissions(client, db_session):
    owner = User(username="owner2", email="o2@example.com", password_hash="x")
    other = User(username="other2", email="other2@example.com", password_hash="x")
    db_session.add_all([owner, other])
    await db_session.commit()
    await db_session.refresh(owner)
    await db_session.refresh(other)

    r = Recipe(title="UpR", owner_id=owner.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    token_other = create_access_token({"sub": str(other.id)})

    # other cannot update -> 403
    resp = await client.put(f"/api/v1/recipes/{r.id}", json={"title": "X"}, headers={"Authorization": f"Bearer {token_other}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_tags_add_remove_and_conflicts(client, db_session):
    u = User(username="tagu", email="tag@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    r = Recipe(title="TagR", owner_id=u.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    token = create_access_token({"sub": str(u.id)})

    # add tag
    resp = await client.post(f"/api/v1/recipes/{r.id}/tags", json={"tag_name": "t1"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201

    # add duplicate tag -> 400
    resp2 = await client.post(f"/api/v1/recipes/{r.id}/tags", json={"tag_name": "t1"}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 400

    # remove non-existent tag id -> 404
    resp3 = await client.delete(f"/api/v1/recipes/{r.id}/tags/999", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 404

    # remove existing tag
    # get tag id
    tag = await db_session.execute(select(RecipeTag).where(RecipeTag.tag_name == "t1"))
    tag_obj = tag.scalars().first()
    resp4 = await client.delete(f"/api/v1/recipes/{r.id}/tags/{tag_obj.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp4.status_code == 204
