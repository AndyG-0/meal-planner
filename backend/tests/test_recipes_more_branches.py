import pytest
from app.utils.auth import get_password_hash
from app.models import User, Recipe, Group, GroupMember
from datetime import datetime


@pytest.mark.asyncio
async def test_update_recipe_as_owner_succeeds(client, test_user, test_token, db_session):
    r = Recipe(title="OwnUp", owner_id=test_user.id, ingredients=[{"name": "a", "quantity": 1, "unit": "cup"}], instructions=["step"], visibility="private")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    resp = await client.put(f"/api/v1/recipes/{r.id}", json={"title": "OwnUp2", "visibility": "public"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "OwnUp2"
    assert body["visibility"] == "public"


@pytest.mark.asyncio
async def test_group_member_access_non_admin_can_view_but_not_edit(client, db_session, test_user, test_token):
    # owner creates group and recipe
    owner = User(username="gowner2", email="go2@example.com", password_hash=get_password_hash("p"))
    db_session.add(owner)
    await db_session.commit()
    await db_session.refresh(owner)

    group = Group(name="GM", owner_id=owner.id)
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    r = Recipe(title="GroupOnly", owner_id=owner.id, visibility="group", group_id=group.id, ingredients=[], instructions=[])
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # add test_user as member (not admin)
    gm = GroupMember(group_id=group.id, user_id=test_user.id, role="member", permissions={})
    db_session.add(gm)
    await db_session.commit()

    # member can view
    resp = await client.get(f"/api/v1/recipes/{r.id}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200

    # but cannot edit
    resp2 = await client.put(f"/api/v1/recipes/{r.id}", json={"title": "BadEdit"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 403


@pytest.mark.asyncio
async def test_list_recipes_no_results_pagination(client, test_user, test_token, db_session):
    # Ensure there are no recipes for this unique search
    resp = await client.get("/api/v1/recipes?search=ThisShouldNotExist&limit=5&page=1", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["pagination"]["total"] == 0 or len(body["items"]) == 0


@pytest.mark.asyncio
async def test_get_recipe_not_found_returns_404(client, test_token):
    resp = await client.get("/api/v1/recipes/999999", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 404
