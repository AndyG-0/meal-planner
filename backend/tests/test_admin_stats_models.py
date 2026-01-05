import pytest
from app.utils.auth import create_access_token
from app.models import User, Recipe, Group


@pytest.mark.asyncio
async def test_admin_stats_counts(client, db_session):
    admin = User(username="statadmin", email="sa@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    await db_session.commit()
    token = create_access_token({"sub": str(admin.id)})

    # create users, recipes, groups
    u1 = User(username="u1", email="u1@example.com", password_hash="x")
    db_session.add(u1)
    await db_session.commit()
    await db_session.refresh(u1)

    g = Group(name="G", owner_id=u1.id)
    db_session.add(g)
    r = Recipe(title="RS", owner_id=u1.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()

    resp = await client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_users"] >= 1
    assert data["total_recipes"] >= 1


@pytest.mark.asyncio
async def test_get_openai_models_no_key(client, db_session):
    admin = User(username="modadmin", email="ma@example.com", password_hash="x", is_admin=True)
    db_session.add(admin)
    await db_session.commit()
    token = create_access_token({"sub": str(admin.id)})

    # Ensure no settings present (delete any)
    from sqlalchemy import text

    await db_session.execute(text("DELETE FROM openai_settings"))
    await db_session.commit()

    resp = await client.get("/api/v1/admin/openai-models", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400