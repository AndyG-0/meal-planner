import pytest
from app.models import Recipe


@pytest.mark.asyncio
async def test_owner_delete_nonexistent_tag_returns_404(client, test_user, test_token, db_session):
    r = Recipe(title="NoTag", owner_id=test_user.id, ingredients=[], instructions=[], visibility="public")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    # Owner deleting a tag that doesn't exist should return 404
    resp = await client.delete(f"/api/v1/recipes/{r.id}/tags/99999", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 404
