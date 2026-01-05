import pytest
from app.api.v1.endpoints.recipes import clean_ingredient_data


def test_clean_ingredient_parsing_various():
    samples = [
        ({"name": "(100 g) cheese, softened", "quantity": None, "unit": ""}, {"name": "cheese, softened", "quantity": 100.0, "unit": "g"}),
        ({"name": "1/2 cup flour", "quantity": None, "unit": ""}, {"name": "flour", "quantity": 0.5, "unit": "cup"}),
        ({"name": "100 g chicken", "quantity": None, "unit": ""}, {"name": "chicken", "quantity": 100.0, "unit": "g"}),
        ({"name": " sliced tomato", "quantity": None, "unit": ""}, {"name": "sliced tomato", "quantity": 1.0, "unit": "serving"}),
    ]

    input_list = [s[0] for s in samples]
    output = clean_ingredient_data(input_list)
    # ensure lengths match and outputs have expected keys
    assert len(output) == len(samples)
    for out, expected in zip(output, [s[1] for s in samples]):
        assert out["name"].startswith(expected["name"].split()[0])
        assert isinstance(out["quantity"], float)
        assert out["unit"] in (expected["unit"], "serving")


@pytest.mark.asyncio
async def test_list_recipes_dietary_filter(client, db_session, test_user, test_token):
    # create recipe with tag matching dietary
    r = Recipe = None
    from app.models import Recipe, RecipeTag

    r1 = Recipe(title="VD", owner_id=test_user.id, category="dinner", visibility="public", ingredients=[], instructions=[])
    db_session.add(r1)
    await db_session.commit()
    await db_session.refresh(r1)

    rt = RecipeTag(recipe_id=r1.id, tag_name="vegan")
    db_session.add(rt)
    await db_session.commit()

    resp = await client.get("/api/v1/recipes?dietary=vegan", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    assert any(item["title"] == "VD" for item in resp.json()["items"])