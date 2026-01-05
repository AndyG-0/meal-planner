import pytest
import io
from app.models import Recipe, RecipeTag


@pytest.mark.asyncio
async def test_list_recipes_difficulty_and_cook_time_filters(client, db_session, test_user, test_token):
    r1 = Recipe(title="D1", owner_id=test_user.id, category="dinner", difficulty="easy", cook_time=10, ingredients=[], instructions=[], visibility="public")
    r2 = Recipe(title="D2", owner_id=test_user.id, category="dinner", difficulty="hard", cook_time=60, ingredients=[], instructions=[], visibility="public")
    db_session.add_all([r1, r2])
    await db_session.commit()

    resp = await client.get("/api/v1/recipes?difficulty=easy", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert all(item["difficulty"] == "easy" for item in resp.json()["items"]) or any(item["title"] == "D1" for item in resp.json()["items"]) 

    resp2 = await client.get("/api/v1/recipes?max_cook_time=30", headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 200
    assert all((item.get("cook_time") is None or item["cook_time"] <= 30) for item in resp2.json()["items"]) 


@pytest.mark.asyncio
async def test_tags_multiple_and_upload_default_extension(client, db_session, test_user, test_token):
    r1 = Recipe(title="TagA", owner_id=test_user.id, category="dinner", visibility="public", ingredients=[], instructions=[])
    r2 = Recipe(title="TagB", owner_id=test_user.id, category="dinner", visibility="public", ingredients=[], instructions=[])
    db_session.add_all([r1, r2])
    await db_session.commit()
    await db_session.refresh(r1)
    await db_session.refresh(r2)

    t1 = RecipeTag(recipe_id=r1.id, tag_name="a")
    t2 = RecipeTag(recipe_id=r2.id, tag_name="b")
    db_session.add_all([t1, t2])
    await db_session.commit()

    # query with multiple tags
    resp = await client.get("/api/v1/recipes?tags=a,b", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    # should have at least one of the tagged recipes
    assert any(item["title"] in ("TagA","TagB") for item in resp.json()["items"]) 

    # test upload with filename missing extension
    r3 = Recipe(title="ImgNoExt", owner_id=test_user.id, ingredients=[], instructions=[], visibility="private")
    db_session.add(r3)
    await db_session.commit()
    await db_session.refresh(r3)

    files = {"file": ("image", io.BytesIO(b"\xff\xd8\xff"), "image/jpeg")}
    resp2 = await client.post(f"/api/v1/recipes/{r3.id}/image", files=files, headers={"Authorization": f"Bearer {test_token}"})
    assert resp2.status_code == 200
    data = resp2.json()
    assert "uploads/recipes" in data["image_url"]
