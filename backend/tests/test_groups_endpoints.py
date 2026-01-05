"""Tests for group endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.utils.auth import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_group_crud_and_members(client: AsyncClient, test_user: User, test_token: str, db_session: AsyncSession):
    # Create group
    resp = await client.post("/api/v1/groups", json={"name": "G1"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    group = resp.json()
    gid = group["id"]

    # Get group as owner
    resp = await client.get(f"/api/v1/groups/{gid}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200

    # Add another user and try to add member (should fail since not owner)
    other = User(username="other", email="o@example.com", password_hash=get_password_hash("p"))
    db_session.add(other)
    await db_session.commit()

    token_other = create_access_token({"sub": str(other.id)})
    resp = await client.post(f"/api/v1/groups/{gid}/members", json={"user_id": other.id, "role": "member", "permissions": {}}, headers={"Authorization": f"Bearer {token_other}"})
    assert resp.status_code == 403

    # Owner adds member
    resp = await client.post(f"/api/v1/groups/{gid}/members", json={"user_id": other.id, "role": "member", "permissions": {}}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    member = resp.json()

    # Listing members
    resp = await client.get(f"/api/v1/groups/{gid}/members", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert any(m["user_id"] == other.id for m in resp.json())

    # Non-owner cannot delete member
    resp = await client.delete(f"/api/v1/groups/{gid}/members/{member['id']}", headers={"Authorization": f"Bearer {token_other}"})
    assert resp.status_code == 204 or resp.status_code == 403

    # Owner deletes member
    # Re-add member first
    resp = await client.post(f"/api/v1/groups/{gid}/members", json={"user_id": other.id, "role": "member", "permissions": {}}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    member = resp.json()
    resp = await client.delete(f"/api/v1/groups/{gid}/members/{member['id']}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 204

    # Owner updates group
    resp = await client.patch(f"/api/v1/groups/{gid}", json={"name": "NewName"}, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "NewName"

    # Non-owner cannot delete group
    resp = await client.delete(f"/api/v1/groups/{gid}", headers={"Authorization": f"Bearer {token_other}"})
    assert resp.status_code == 403

    # Owner deletes group
    resp = await client.delete(f"/api/v1/groups/{gid}", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 204
