"""Tests for OpenAIService create/update behavior and tag categorization."""

import pytest

from app.services.openai_service import OpenAIService
from app.models import Recipe, RecipeTag, User
from app.utils.auth import get_password_hash
from sqlalchemy import select


@pytest.mark.asyncio
async def test_create_recipe_success(db_session, test_user):
    service = OpenAIService(db_session)

    # Mock search_images to return a URL
    async def _mock_search_images(query, max_results=1):
        return [{"url": "http://example.com/image.jpg"}]

    service.search_images = _mock_search_images

    recipe_data = {
        "name": "AI Pancakes",
        "description": "Tasty",
        "ingredients": [{"name": "flour", "quantity": 2, "unit": "cup"}],
        "instructions": ["mix", "cook"],
        "prep_time": 10,
        "cook_time": 5,
        "servings": 2,
        "difficulty": "easy",
        "category": "breakfast",
        "tags": ["Vegan", "Italian"],
    }

    recipe = await service.create_recipe(recipe_data, test_user)

    assert isinstance(recipe, Recipe)
    assert recipe.title == "AI Pancakes"
    assert recipe.image_url and "example.com" in recipe.image_url

    # Tags should have been added
    result = await db_session.execute(
        select(RecipeTag).where(RecipeTag.recipe_id == recipe.id)
    )
    tags = result.scalars().all()
    assert len(tags) == 2
    # Check categories mapped
    cats = {t.tag_category for t in tags}
    assert "dietary" in cats or "cuisine" in cats or "other" in cats


@pytest.mark.asyncio
async def test_create_recipe_invalid_ingredient_type(db_session, test_user):
    service = OpenAIService(db_session)

    recipe_data = {
        "name": "Bad",
        "ingredients": ["not-a-dict"],
        "instructions": [],
        "prep_time": 1,
        "cook_time": 1,
        "servings": 1,
    }

    with pytest.raises(ValueError):
        await service.create_recipe(recipe_data, test_user)


@pytest.mark.asyncio
async def test_create_recipe_measurement_in_name(db_session, test_user):
    service = OpenAIService(db_session)

    recipe_data = {
        "name": "Bad",
        "ingredients": [{"name": "1/2 cup sugar", "quantity": 0.5, "unit": "cup"}],
        "instructions": [],
        "prep_time": 1,
        "cook_time": 1,
        "servings": 1,
    }

    with pytest.raises(ValueError):
        await service.create_recipe(recipe_data, test_user)


@pytest.mark.asyncio
async def test_update_recipe_errors(db_session, test_user):
    service = OpenAIService(db_session)

    # Missing recipe_id
    with pytest.raises(ValueError):
        await service.update_recipe({}, test_user)

    # Non-existent recipe
    with pytest.raises(ValueError):
        await service.update_recipe({"recipe_id": 9999}, test_user)


@pytest.mark.asyncio
async def test_categorize_tag():
    s = OpenAIService(None)
    assert s._categorize_tag("vegan") == "dietary"
    assert s._categorize_tag("italian") == "cuisine"
    assert s._categorize_tag("breakfast") == "meal_type"
    assert s._categorize_tag("air-fryer") == "cooking_method"
    assert s._categorize_tag("something-unknown") == "other"
