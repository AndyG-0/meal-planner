import pytest

from app.models import User
from app.utils.auth import create_access_token


@pytest.mark.asyncio
async def test_feature_toggle_duplicate_and_delete_not_found(client, db_session):
    admin = User(username="ftdup", email="ftd@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    await db_session.commit()

    token = create_access_token({"sub": str(admin.id)})

    payload = {"feature_key": "dup_test", "feature_name": "Dup Test", "is_enabled": True}
    resp = await client.post("/api/v1/admin/feature-toggles", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201

    # Duplicate creation should fail
    resp2 = await client.post("/api/v1/admin/feature-toggles", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 400

    # Delete missing toggle should be 404
    resp3 = await client.delete("/api/v1/admin/feature-toggles/not_exist", headers={"Authorization": f"Bearer {token}"})
    assert resp3.status_code == 404
