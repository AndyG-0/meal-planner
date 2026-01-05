import pytest


@pytest.mark.asyncio
async def test_clean_ingredient_in_list_recipes(client, db_session, test_user, test_token):
    # Create a recipe with a measurement in the ingredient name
    from app.models import Recipe

    r = Recipe(
        title="Bad Ingredient",
        owner_id=test_user.id,
        ingredients=[{"name": "1/2 cup flour", "quantity": 1, "unit": "serving"}],
        instructions=["do it"],
        prep_time=5,
        cook_time=5,
        serving_size=1,
    )
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    resp = await client.get("/api/v1/recipes", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["total"] >= 1

    # Find our recipe in results
    items = data["items"]
    found = [it for it in items if it["title"] == "Bad Ingredient"]
    assert found, "Bad Ingredient recipe not found"
    ingredient = found[0]["ingredients"][0]
    assert ingredient["name"] == "flour"
    assert ingredient["unit"] == "cup"
    assert float(ingredient["quantity"]) == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_list_recipes_filters_and_pagination(client, db_session, test_user, test_token):
    from app.models import Recipe, RecipeTag

    # Create several recipes
    r1 = Recipe(title="Pizza", owner_id=test_user.id, ingredients=[], instructions=["a"], prep_time=10, cook_time=15, serving_size=2, category="dinner", difficulty="easy")
    r2 = Recipe(title="Cookie", owner_id=test_user.id, ingredients=[], instructions=["b"], prep_time=5, cook_time=10, serving_size=4, category="dessert", difficulty="medium")
    db_session.add_all([r1, r2])
    await db_session.commit()
    await db_session.refresh(r1)
    await db_session.refresh(r2)

    # Add a tag to Pizza
    tag = RecipeTag(recipe_id=r1.id, tag_name="italian", tag_category="cuisine")
    db_session.add(tag)
    await db_session.commit()

    # Filter by category
    resp = await client.get("/api/v1/recipes?category=dinner", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(i["title"] == "Pizza" for i in items)

    # Filter by difficulty
    resp = await client.get("/api/v1/recipes?difficulty=easy", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(i["title"] == "Pizza" for i in items)

    # Filter by prep and cook time
    resp = await client.get("/api/v1/recipes?max_prep_time=10&max_cook_time=15", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(i["title"] == "Pizza" for i in items)

    # Filter by tags
    resp = await client.get("/api/v1/recipes?tags=italian", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(i["title"] == "Pizza" for i in items)


@pytest.mark.asyncio
async def test_get_all_tags_grouping(client, db_session, test_user, test_token):
    from app.models import Recipe, RecipeTag

    r = Recipe(title="T", owner_id=test_user.id, ingredients=[], instructions=["a"], prep_time=1, cook_time=1, serving_size=1)
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    tags = [
        RecipeTag(recipe_id=r.id, tag_name="vegan", tag_category="dietary"),
        RecipeTag(recipe_id=r.id, tag_name="italian", tag_category="cuisine"),
        RecipeTag(recipe_id=r.id, tag_name="baking", tag_category="cooking_method"),
    ]
    db_session.add_all(tags)
    await db_session.commit()

    resp = await client.get("/api/v1/recipes/tags/all", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "dietary" in data and any(t["name"] == "vegan" for t in data["dietary"])
    assert "cuisine" in data and any(t["name"] == "italian" for t in data["cuisine"])


@pytest.mark.asyncio
async def test_favorites_listing(client, db_session, test_user, test_token):
    from app.models import Recipe, UserFavorite

    r = Recipe(title="Fav", owner_id=test_user.id, ingredients=[], instructions=["x"], prep_time=1, cook_time=1, serving_size=1)
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    fav = UserFavorite(user_id=test_user.id, recipe_id=r.id)
    db_session.add(fav)
    await db_session.commit()

    resp = await client.get("/api/v1/recipes/favorites", headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
    items = resp.json()
    assert any(i["title"] == "Fav" for i in items)
