import pytest

from app.models import FeatureToggle, OpenAISettings, User
from app.services.openai_service import OpenAIService


@pytest.mark.asyncio
async def test_get_system_prompt_uses_settings(db_session):
    # enable feature toggle and settings
    ft = FeatureToggle(feature_key="ai_recipe_creation", feature_name="AI", is_enabled=True)
    s = OpenAISettings(id=1, api_key="sk-test", system_prompt="Custom Prompt")
    db_session.add_all([ft, s])
    await db_session.commit()

    service = OpenAIService(db_session)
    await service.initialize()

    user = User(username="ou", email="ou@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    prompt = await service.get_system_prompt(user)
    assert "Custom Prompt" in prompt


@pytest.mark.asyncio
async def test_get_tags_and_dietary_context_returns_strings(db_session):
    service = OpenAIService(db_session)
    # _get_tags_context returns default when no tags
    user = User(username="u1", email="u1@example.com", password_hash="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    tags_ctx = await service._get_tags_context(user)
    assert "RECIPE TAGS" in tags_ctx

    # dietary context when user has prefs
    user.dietary_preferences = ["vegan"]
    db_session.add(user)
    await db_session.commit()
    dc = await service._get_dietary_preferences_context(user, use_dietary_preferences=True)
    assert "USER DIETARY PREFERENCES" in dc


def test_get_tools_definition():
    service = OpenAIService(None)
    tools = service.get_tools_definition()
    assert isinstance(tools, list)
    assert any(t["function"]["name"] == "create_recipe" for t in tools)
