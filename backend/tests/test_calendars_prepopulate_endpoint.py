from datetime import datetime

import pytest

from app.models import Calendar, Recipe, User
from app.utils.auth import create_access_token


@pytest.mark.asyncio
async def test_prepopulate_endpoint_success(client, db_session, test_user, test_token):
    u = test_user
    cal = Calendar(name="EP", owner_id=u.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    # create recipes for lunch
    r1 = Recipe(title="L1", owner_id=u.id, category="lunch", visibility="public", ingredients=[], instructions=[])
    r2 = Recipe(title="L2", owner_id=u.id, category="lunch", visibility="public", ingredients=[], instructions=[])
    db_session.add_all([r1, r2])
    await db_session.commit()

    start = datetime.utcnow().isoformat()
    payload = {"start_date": start, "period": "day", "meal_types": ["lunch"], "snacks_per_day": 0, "desserts_per_day": 0, "use_dietary_preferences": False, "avoid_duplicates": True}

    resp = await client.post(f"/api/v1/calendars/{cal.id}/prepopulate", json=payload, headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["meals_created"] >= 1


@pytest.mark.asyncio
async def test_update_calendar_permissions(client, db_session, test_user, test_token):
    owner = test_user
    cal = Calendar(name="UP", owner_id=owner.id)
    db_session.add(cal)
    await db_session.commit()
    await db_session.refresh(cal)

    # other user cannot update
    other = User(username="cother", email="co@example.com", password_hash="x")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    # attempt update as other
    token_other = create_access_token({"sub": str(other.id)})
    resp = await client.put(f"/api/v1/calendars/{cal.id}", json={"name": "NewName"}, headers={"Authorization": f"Bearer {token_other}"})
    assert resp.status_code == 403

    # owner can update
    token_owner = create_access_token({"sub": str(owner.id)})
    resp2 = await client.put(f"/api/v1/calendars/{cal.id}", json={"name": "NewName"}, headers={"Authorization": f"Bearer {token_owner}"})
    assert resp2.status_code == 200
    assert resp2.json()["name"] == "NewName"
