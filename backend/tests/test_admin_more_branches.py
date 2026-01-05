import pytest
from app.utils.auth import create_access_token
from app.models import User, Recipe, Calendar, Group, FeatureToggle


@pytest.mark.asyncio
async def test_admin_stats_and_recipe_filters(client, db_session):
    admin = User(username="adm", email="adm@example.com", password_hash="x", is_admin=True)
    u = User(username="ru", email="ru@example.com", password_hash="x")
    db_session.add_all([admin, u])
    await db_session.commit()
    await db_session.refresh(u)

    # create recipes with different visibility
    r1 = Recipe(title="PubR", owner_id=u.id, visibility="public", ingredients=[], instructions=[])
    r2 = Recipe(title="GrpR", owner_id=u.id, visibility="group", ingredients=[], instructions=[])
    r3 = Recipe(title="PrivR", owner_id=u.id, visibility="private", ingredients=[], instructions=[])
    db_session.add_all([r1, r2, r3])

    # calendars and groups
    cal = Calendar(name="C1", owner_id=u.id)
    grp = Group(name="G1", owner_id=u.id)
    db_session.add_all([cal, grp])
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    # stats
    resp = await client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_users"] >= 2
    assert data["total_recipes"] >= 3

    # list recipes filter
    resp2 = await client.get("/api/v1/admin/recipes?visibility=public", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    assert any(item["title"] == "PubR" for item in resp2.json())


@pytest.mark.asyncio
async def test_admin_recipes_filters_complex(client, db_session):
    admin = User(username="admcf", email="admcf@example.com", password_hash="x", is_admin=True)
    u = User(username="u2", email="u2@example.com", password_hash="x")
    db_session.add_all([admin, u])
    await db_session.commit()
    await db_session.refresh(u)

    r1 = Recipe(title="Filter1", owner_id=u.id, category="dinner", difficulty="easy", visibility="public", ingredients=[], instructions=[])
    r2 = Recipe(title="Filter2", owner_id=u.id, category="breakfast", difficulty="hard", visibility="private", ingredients=[], instructions=[])
    db_session.add_all([r1, r2])
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    resp = await client.get("/api/v1/admin/recipes?search=Filter1", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(item["title"] == "Filter1" for item in resp.json())

    resp2 = await client.get("/api/v1/admin/recipes?category=breakfast", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    # admin list returns a subset of fields; verify expected titles are present
    assert any(item["title"] == "Filter2" for item in resp2.json())

    resp3 = await client.get("/api/v1/admin/recipes?visibility=private", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 200
    assert all(item["visibility"] == "private" for item in resp3.json())


@pytest.mark.asyncio
async def test_admin_user_update_conflicts_and_self_delete(client, db_session):
    admin = User(username="adm2", email="adm2@example.com", password_hash="x", is_admin=True)
    u1 = User(username="u1", email="u1@example.com", password_hash="x")
    u2 = User(username="u2", email="u2@example.com", password_hash="x")
    db_session.add_all([admin, u1, u2])
    await db_session.commit()
    await db_session.refresh(u1)

    token = create_access_token({"sub": str(admin.id)})

    # attempt to update u1 email to u2's email -> 400
    resp = await client.patch(f"/api/v1/admin/users/{u1.id}", json={"email": "u2@example.com"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400

    # admin cannot delete self
    resp2 = await client.delete(f"/api/v1/admin/users/{admin.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_feature_toggles_crud(client, db_session):
    admin = User(username="togadmin", email="ta@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    # create toggle
    resp = await client.post("/api/v1/admin/feature-toggles", json={"feature_key": "f1", "feature_name": "F1", "is_enabled": False}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["feature_key"] == "f1"

    # duplicate create -> 400
    resp2 = await client.post("/api/v1/admin/feature-toggles", json={"feature_key": "f1", "feature_name": "F1", "is_enabled": False}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 400

    # get toggle
    resp3 = await client.get("/api/v1/admin/feature-toggles/f1", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 200

    # patch toggle
    resp4 = await client.patch("/api/v1/admin/feature-toggles/f1", json={"is_enabled": True}, headers={"Authorization": f"Bearer {token}"})
    assert resp4.status_code == 200
    assert resp4.json()["is_enabled"] is True

    # delete toggle
    resp5 = await client.delete("/api/v1/admin/feature-toggles/f1", headers={"Authorization": f"Bearer {token}"})
    assert resp5.status_code == 204

    # get after delete -> 404
    resp6 = await client.get("/api/v1/admin/feature-toggles/f1", headers={"Authorization": f"Bearer {token}"})
    assert resp6.status_code == 404


@pytest.mark.asyncio
async def test_openai_and_session_settings(client, db_session):
    admin = User(username="sadmin", email="s@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    # get openai settings (should create default)
    resp = await client.get("/api/v1/admin/openai-settings", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    s = resp.json()
    assert "has_api_key" in s

    # update openai settings
    resp2 = await client.patch("/api/v1/admin/openai-settings", json={"api_key": "sk-test"}, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    s2 = resp2.json()
    assert s2["has_api_key"] is True

    # session settings get/create
    resp3 = await client.get("/api/v1/admin/session-settings", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 200

    # patch session settings
    resp4 = await client.patch("/api/v1/admin/session-settings", json={"session_ttl_value": 10, "session_ttl_unit": "days"}, headers={"Authorization": f"Bearer {token}"})
    assert resp4.status_code == 200
    assert resp4.json()["session_ttl_value"] == 10
