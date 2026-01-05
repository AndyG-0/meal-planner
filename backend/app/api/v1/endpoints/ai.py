"""AI-powered recipe creation endpoints."""

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, get_db
from app.models import RecipeTag, User, UserFavorite
from app.schemas import AIChatRequest, AIChatResponse, RecipeResponse, RecipeTagResponse
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    chat_request: AIChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AIChatResponse:
    """
    Chat with AI assistant for recipe creation.

    The AI can help create recipes, suggest modifications, and handle dietary restrictions.
    It will ask for user confirmation before making any database changes.
    """
    logger.info(
        f"AI chat request from user {current_user.id}, {len(chat_request.messages)} messages, use_dietary_preferences={chat_request.use_dietary_preferences}"
    )
    try:
        service = OpenAIService(db)
        await service.initialize()

        messages = []
        for msg in chat_request.messages:
            message_dict = {"role": msg.role, "content": msg.content}

            # Add tool_call_id for tool messages
            if msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id

            # Add tool_calls for assistant messages that have them
            if msg.tool_calls:
                # Convert our tool_calls format to OpenAI's format
                message_dict["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": json.dumps(tc["arguments"])},
                    }
                    for tc in msg.tool_calls
                ]

            messages.append(message_dict)

        logger.debug(
            f"Prepared messages for OpenAI: {json.dumps([{k: v for k, v in m.items() if k != 'content'} for m in messages], indent=2)}"
        )

        result = await service.chat(messages, current_user, chat_request.use_dietary_preferences)

        logger.info(
            f"AI chat response: message_len={len(result['message'])}, has_tool_calls={bool(result.get('tool_calls'))}"
        )

        return AIChatResponse(message=result["message"], tool_calls=result.get("tool_calls"))

    except ValueError as e:
        logger.warning(f"AI chat validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"AI chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI service error: {str(e)}"
        )


@router.post("/execute-tool", response_model=dict)
async def execute_ai_tool(
    tool_call: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    Execute an AI tool call (create_recipe, update_recipe, list_user_recipes).

    This endpoint is called after the user confirms an AI action.
    """
    logger.info(f"Execute tool request from user {current_user.id}, tool: {tool_call.get('name')}")
    logger.debug(f"Tool call data: {tool_call}")

    try:
        service = OpenAIService(db)
        await service.initialize()

        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})

        if tool_name == "create_recipe":
            recipe = await service.create_recipe(arguments, current_user)

            # Load tags eagerly to avoid lazy loading issues
            tag_result = await db.execute(select(RecipeTag).where(RecipeTag.recipe_id == recipe.id))
            recipe_tags = tag_result.scalars().all()

            # Check if favorited
            favorite_result = await db.execute(
                select(UserFavorite).where(
                    UserFavorite.user_id == current_user.id, UserFavorite.recipe_id == recipe.id
                )
            )
            is_favorited = favorite_result.scalar_one_or_none() is not None

            recipe_response = RecipeResponse(
                id=recipe.id,
                owner_id=recipe.owner_id,
                title=recipe.title,
                description=recipe.description,
                ingredients=recipe.ingredients,
                instructions=recipe.instructions,
                serving_size=recipe.serving_size,
                prep_time=recipe.prep_time,
                cook_time=recipe.cook_time,
                difficulty=recipe.difficulty,
                category=recipe.category,
                nutritional_info=recipe.nutritional_info,
                visibility=recipe.visibility,
                group_id=recipe.group_id,
                is_shared=recipe.is_shared,
                is_public=recipe.is_public,
                image_url=recipe.image_url,
                created_at=recipe.created_at,
                updated_at=recipe.updated_at,
                is_favorite=is_favorited,
                tags=[RecipeTagResponse.model_validate(tag) for tag in recipe_tags],
            )

            return {"success": True, "action": "create", "recipe": recipe_response.model_dump()}

        elif tool_name == "update_recipe":
            recipe = await service.update_recipe(arguments, current_user)

            # Load tags eagerly to avoid lazy loading issues
            tag_result = await db.execute(select(RecipeTag).where(RecipeTag.recipe_id == recipe.id))
            recipe_tags = tag_result.scalars().all()

            # Check if favorited
            favorite_result = await db.execute(
                select(UserFavorite).where(
                    UserFavorite.user_id == current_user.id, UserFavorite.recipe_id == recipe.id
                )
            )
            is_favorited = favorite_result.scalar_one_or_none() is not None

            recipe_response = RecipeResponse(
                id=recipe.id,
                owner_id=recipe.owner_id,
                title=recipe.title,
                description=recipe.description,
                ingredients=recipe.ingredients,
                instructions=recipe.instructions,
                serving_size=recipe.serving_size,
                prep_time=recipe.prep_time,
                cook_time=recipe.cook_time,
                difficulty=recipe.difficulty,
                category=recipe.category,
                nutritional_info=recipe.nutritional_info,
                visibility=recipe.visibility,
                group_id=recipe.group_id,
                is_shared=recipe.is_shared,
                is_public=recipe.is_public,
                image_url=recipe.image_url,
                created_at=recipe.created_at,
                updated_at=recipe.updated_at,
                is_favorite=is_favorited,
                tags=[RecipeTagResponse.model_validate(tag) for tag in recipe_tags],
            )

            return {"success": True, "action": "update", "recipe": recipe_response.model_dump()}

        elif tool_name == "list_user_recipes":
            limit = arguments.get("limit", 10)
            recipes = await service.list_user_recipes(current_user, limit)
            return {"success": True, "action": "list", "recipes": recipes}

        elif tool_name == "search_web":
            query = arguments.get("query")
            max_results = arguments.get("max_results", 5)
            logger.info(f"Executing search_web: query='{query}', max_results={max_results}")
            results = await service.search_web(query, max_results)
            logger.info(f"Search returned {len(results)} results")
            return {"success": True, "action": "search", "results": results}

        elif tool_name == "fetch_url":
            url = arguments.get("url")
            logger.info(f"Executing fetch_url: {url}")
            content = await service.fetch_url(url)
            logger.info(f"URL fetch successful, content length: {len(content.get('content', ''))}")
            logger.debug(f"Fetched content preview: {content.get('content', '')[:500]}")
            return {"success": True, "action": "fetch", "content": content}

        elif tool_name == "search_images":
            query = arguments.get("query")
            max_results = arguments.get("max_results", 5)
            logger.info(f"Executing search_images: query='{query}', max_results={max_results}")
            results = await service.search_images(query, max_results)
            logger.info(f"Image search returned {len(results)} results")
            return {"success": True, "action": "search_images", "results": results}

        else:
            logger.warning(f"Unknown tool requested: {tool_name}")
            raise ValueError(f"Unknown tool: {tool_name}")

    except ValueError as e:
        logger.warning(f"Tool execution validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Tool execution error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution error: {str(e)}",
        )


@router.get("/status")
async def ai_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Check if AI recipe creation is available and configured."""
    try:
        service = OpenAIService(db)
        await service.initialize()
        return {"available": True, "model": service.settings.model if service.settings else "gpt-4"}
    except ValueError as e:
        return {"available": False, "error": str(e)}


@router.get("/search-images")
async def search_images(
    query: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    max_results: int = 10,
) -> dict:
    """
    Search for recipe/food images using SearXNG.

    This endpoint allows users to search for images when adding or editing recipes.
    """
    logger.info(
        f"Image search request from user {current_user.id}, query: '{query}', max_results: {max_results}"
    )

    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Search query is required"
        )

    try:
        service = OpenAIService(db)
        await service.initialize()

        results = await service.search_images(query.strip(), max_results)

        logger.info(f"Image search successful, returning {len(results)} results")
        return {"success": True, "query": query, "results": results}

    except ValueError as e:
        logger.warning(f"Image search validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Image search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image search error: {str(e)}",
        )
