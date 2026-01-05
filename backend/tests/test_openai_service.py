"""Tests for OpenAIService initialization and prompt helpers."""

import pytest

from app.models import FeatureToggle, OpenAISettings, Recipe, RecipeTag, User
from app.services.openai_service import OpenAIService


@pytest.mark.asyncio
async def test_initialize_checks_feature_toggle(db_session):
    service = OpenAIService(db_session)

    # No toggle present
    with pytest.raises(ValueError):
        await service.initialize()

    # Toggle present but not enabled
    db_session.add(
        FeatureToggle(feature_key="ai_recipe_creation", feature_name="AI", is_enabled=False)
    )
    await db_session.commit()

    with pytest.raises(ValueError):
        await service.initialize()


@pytest.mark.asyncio
async def test_initialize_checks_api_key(db_session):
    # Toggle enabled but no settings
    db_session.add(
        FeatureToggle(feature_key="ai_recipe_creation", feature_name="AI", is_enabled=True)
    )
    await db_session.commit()

    service = OpenAIService(db_session)
    with pytest.raises(ValueError):
        await service.initialize()

    # Add settings but without api_key
    db_session.add(OpenAISettings(id=1, api_key=None))
    await db_session.commit()

    with pytest.raises(ValueError):
        await service.initialize()


@pytest.mark.asyncio
async def test_initialize_success_with_api_key(db_session):
    db_session.add(
        FeatureToggle(feature_key="ai_recipe_creation", feature_name="AI", is_enabled=True)
    )
    db_session.add(OpenAISettings(id=1, api_key="fake-key"))
    await db_session.commit()

    service = OpenAIService(db_session)
    await service.initialize()
    assert service.client is not None


@pytest.mark.asyncio
async def test_get_system_prompt_includes_tags_and_dietary(db_session):
    # Prepare toggle/settings so service initializes settings attr
    db_session.add(OpenAISettings(id=1, api_key="fake-key", system_prompt=None))

    # Create a user with dietary preferences
    user = User(
        username="u2", email="u2@example.com", dietary_preferences=["vegan"], password_hash="x"
    )
    db_session.add(user)
    await db_session.commit()

    # Create a public recipe with a tag
    r = Recipe(
        title="Vegan Salad",
        owner_id=user.id,
        visibility="public",
        category="lunch",
        ingredients=[],
        instructions=[],
    )
    db_session.add(r)
    await db_session.commit()

    tag = RecipeTag(recipe_id=r.id, tag_name="vegan", tag_category="dietary")
    db_session.add(tag)
    await db_session.commit()

    service = OpenAIService(db_session)
    # Manually set settings for prompt tests
    service.settings = OpenAISettings(id=1, api_key="fake", system_prompt=None)

    prompt = await service.get_system_prompt(user, use_dietary_preferences=True)
    assert (
        "USER DIETARY PREFERENCES" in prompt
        or "This user has not set any dietary preferences" in prompt
    )
    assert "RECIPE TAGS" in prompt
