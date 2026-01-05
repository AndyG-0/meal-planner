import pytest

from app.models import User
from app.services.openai_service import OpenAIService


@pytest.mark.asyncio
async def test_get_system_prompt_includes_dietary_context(db_session):
    # create a user with dietary preferences
    user = User(username="dietuser", email="diet@example.com", password_hash="x", dietary_preferences=["vegan", "gluten-free"])
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    service = OpenAIService(db_session)

    # monkeypatch settings so feature toggle exists
    from app.models import FeatureToggle, OpenAISettings

    ft = FeatureToggle(feature_key="ai_recipe_creation", feature_name="AI", is_enabled=True)
    settings = OpenAISettings(id=1, api_key="sk-test")
    db_session.add_all([ft, settings])
    await db_session.commit()

    await service.initialize()
    prompt = await service.get_system_prompt(user, use_dietary_preferences=True)
    assert "USER DIETARY PREFERENCES" in prompt or "dietary preferences" in prompt.lower()
