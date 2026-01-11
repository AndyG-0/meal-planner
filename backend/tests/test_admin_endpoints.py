"""Tests for admin endpoints (stats and feature toggle CRUD)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Calendar, Group, Recipe, User
from app.utils.auth import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_admin_requires_admin(client: AsyncClient, db_session: AsyncSession):
    # non-admin user
    user = User(
        username="normal", email="normal@example.com", password_hash=get_password_hash("password")
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})

    response = await client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_admin_stats_and_feature_toggle_crud(
    client: AsyncClient, db_session: AsyncSession
):
    # create admin user
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("password"),
        is_admin=True,
    )
    db_session.add(admin)
    await db_session.commit()

    # create some data
    recipe = Recipe(
        title="R1",
        owner_id=admin.id,
        ingredients=[{"name": "x", "quantity": 1, "unit": "unit"}],
        instructions=["a"],
    )
    calendar = Calendar(name="C1", owner_id=admin.id)
    group = Group(name="G1", owner_id=admin.id)
    db_session.add_all([recipe, calendar, group])
    await db_session.commit()

    token = create_access_token(data={"sub": str(admin.id)})

    # Get stats
    response = await client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] >= 1
    assert data["total_recipes"] >= 1
    # Test version field is present and has expected value
    assert "version" in data
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0  # Version should not be empty

    # Feature toggle CRUD
    toggle = {
        "feature_key": "new_feature",
        "feature_name": "New Feature",
        "is_enabled": True,
        "description": "desc",
    }
    resp = await client.post(
        "/api/v1/admin/feature-toggles", json=toggle, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["feature_key"] == "new_feature"

    # Get list
    resp = await client.get(
        "/api/v1/admin/feature-toggles", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert any(t["feature_key"] == "new_feature" for t in resp.json())

    # Get single
    resp = await client.get(
        "/api/v1/admin/feature-toggles/new_feature", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200

    # Patch
    resp = await client.patch(
        "/api/v1/admin/feature-toggles/new_feature",
        json={"is_enabled": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_enabled"] is False

    # Delete
    resp = await client.delete(
        "/api/v1/admin/feature-toggles/new_feature", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 204

    # Not found after delete
    resp = await client.get(
        "/api/v1/admin/feature-toggles/new_feature", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_user_management_and_recipe_admin_endpoints(client: AsyncClient, db_session: AsyncSession):
    # create admin user
    admin = User(
        username="superadmin",
        email="sa@example.com",
        password_hash=get_password_hash("password"),
        is_admin=True,
    )
    db_session.add(admin)
    await db_session.commit()

    # Create some normal users
    u1 = User(username="user1", email="u1@example.com", password_hash=get_password_hash("p"))
    u2 = User(username="user2", email="u2@example.com", password_hash=get_password_hash("p"))
    db_session.add_all([u1, u2])
    await db_session.commit()

    # Create recipe owned by u1
    r = Recipe(title="AdminR", owner_id=u1.id, ingredients=[{"name":"x","quantity":1,"unit":"unit"}], instructions=["a"])
    db_session.add(r)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    # List users
    resp = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(u["username"] == "user1" for u in resp.json())

    # Get user details
    resp = await client.get(f"/api/v1/admin/users/{u1.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # Update user (promote to admin)
    resp = await client.patch(f"/api/v1/admin/users/{u1.id}", json={"is_admin": True}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["is_admin"] is True

    # Update email conflict
    resp = await client.patch(f"/api/v1/admin/users/{u1.id}", json={"email": "u2@example.com"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400

    # Delete user (cannot delete self)
    resp = await client.delete(f"/api/v1/admin/users/{admin.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400

    # Delete another user
    resp = await client.delete(f"/api/v1/admin/users/{u2.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204

    # Admin recipe listing with filters
    resp = await client.get("/api/v1/admin/recipes?category=dinner", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # Get recipe details as admin
    resp = await client.get(f"/api/v1/admin/recipes/{r.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # Admin patch recipe
    resp = await client.patch(f"/api/v1/admin/recipes/{r.id}", json={"title": "AdminUpdated"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "AdminUpdated"

    # Admin delete recipe
    resp = await client.delete(f"/api/v1/admin/recipes/{r.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_openai_settings_and_models(client: AsyncClient, db_session: AsyncSession, monkeypatch):
    # create admin
    admin = User(username="openadmin", email="open@example.com", password_hash=get_password_hash("password"), is_admin=True)
    db_session.add(admin)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    # Initially, get_openai_models should fail (no api key configured)
    resp = await client.get("/api/v1/admin/openai-models", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400

    # Get openai-settings (should create defaults)
    resp = await client.get("/api/v1/admin/openai-settings", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_api_key"] is False
    assert data["searxng_url"] == "http://localhost:8085"

    # Update settings with API key
    resp = await client.patch("/api/v1/admin/openai-settings", json={"api_key": "fake-key"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["has_api_key"] is True

    # Mock AsyncOpenAI to return models
    class FakeModel:
        def __init__(self, id):
            self.id = id
            self.owned_by = "owner"
            self.created = 1

    class FakeModels:
        def __init__(self, data):
            self.data = data

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        class Models:
            @staticmethod
            async def list():
                return FakeModels([FakeModel("gpt-3.5-turbo")])

        @property
        def models(self):
            return self.Models

    monkeypatch.setattr("openai.AsyncOpenAI", FakeClient)

    resp = await client.get("/api/v1/admin/openai-models", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(m["id"].startswith("gpt-3.5") for m in resp.json()["models"])


@pytest.mark.asyncio
async def test_session_settings_get_and_patch(client: AsyncClient, db_session: AsyncSession):
    admin = User(username="sessadmin", email="sess@example.com", password_hash=get_password_hash("password"), is_admin=True)
    db_session.add(admin)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    resp = await client.get("/api/v1/admin/session-settings", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "session_ttl_value" in data

    resp = await client.patch("/api/v1/admin/session-settings", json={"session_ttl_value": 45}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["session_ttl_value"] == 45


@pytest.mark.asyncio
async def test_calendar_and_group_admin_endpoints(client: AsyncClient, db_session: AsyncSession):
    admin = User(username="caladmin", email="cal@example.com", password_hash=get_password_hash("password"), is_admin=True)
    u = User(username="g1", email="g1@example.com", password_hash=get_password_hash("pw"))
    db_session.add_all([admin, u])
    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(u)

    # Create calendar and group
    cal = Calendar(name="MyCal", owner_id=u.id)
    grp = Group(name="MyGroup", owner_id=u.id)
    db_session.add_all([cal, grp])
    await db_session.commit()
    await db_session.refresh(cal)
    await db_session.refresh(grp)

    token = create_access_token({"sub": str(admin.id)})

    # List calendars
    resp = await client.get("/api/v1/admin/calendars", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(c["name"] == "MyCal" for c in resp.json())

    # Get calendar details
    resp = await client.get(f"/api/v1/admin/calendars/{cal.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # Update calendar
    resp = await client.patch(f"/api/v1/admin/calendars/{cal.id}", json={"name": "NewName"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "NewName"

    # Delete calendar
    resp = await client.delete(f"/api/v1/admin/calendars/{cal.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204

    # List groups
    resp = await client.get("/api/v1/admin/groups", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert any(g["name"] == "MyGroup" for g in resp.json())

    # Get group details
    resp = await client.get(f"/api/v1/admin/groups/{grp.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # Update group
    resp = await client.patch(f"/api/v1/admin/groups/{grp.id}", json={"name": "G2"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "G2"

    # Delete group
    resp = await client.delete(f"/api/v1/admin/groups/{grp.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204

    # Try to delete non-existent member
    resp = await client.delete(f"/api/v1/admin/groups/{grp.id}/members/999", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in (404, 204)
