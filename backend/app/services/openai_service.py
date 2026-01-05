"""OpenAI service for AI-powered recipe creation."""

import json
import logging
from typing import Any

import httpx

from openai import AsyncOpenAI
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import FeatureToggle, GroupMember, OpenAISettings, Recipe, RecipeTag, User

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for handling OpenAI interactions."""

    def __init__(self, db: AsyncSession):
        """Initialize OpenAI service."""
        self.db = db
        self.client: AsyncOpenAI | None = None
        self.settings: OpenAISettings | None = None
        logger.info("OpenAIService initialized")

    async def initialize(self) -> None:
        """Initialize the OpenAI client with settings from database."""
        # Check if AI feature is enabled
        result = await self.db.execute(
            select(FeatureToggle).where(FeatureToggle.feature_key == "ai_recipe_creation")
        )
        toggle = result.scalar_one_or_none()
        if not toggle or not toggle.is_enabled:
            raise ValueError("AI recipe creation feature is not enabled")

        # Get OpenAI settings
        settings_result = await self.db.execute(
            select(OpenAISettings).where(OpenAISettings.id == 1)
        )
        self.settings = settings_result.scalar_one_or_none()
        if not self.settings or not self.settings.api_key:
            raise ValueError("OpenAI API key is not configured")

        self.client = AsyncOpenAI(api_key=self.settings.api_key)

    async def get_system_prompt(self, user: User, use_dietary_preferences: bool = True) -> str:
        """Get the system prompt for recipe creation.

        Args:
            user: The current user to personalize the prompt
            use_dietary_preferences: Whether to include dietary preferences
        """
        if self.settings and self.settings.system_prompt:
            return self.settings.system_prompt

        # Get available tags for context
        tags_context = await self._get_tags_context(user)

        # Get user dietary preferences if enabled
        dietary_context = await self._get_dietary_preferences_context(user, use_dietary_preferences)

        # Default system prompt
        base_prompt = """You are a helpful culinary assistant that helps users create and refine recipes.
Your goal is to create detailed, practical recipes that users will love.

When creating recipes, always provide complete information including:
- Recipe name and description
- Ingredients as objects with: name, quantity (as a number), and unit (e.g., "cup", "tbsp", "oz", "g")
- Step-by-step instructions (in a list format)
- Prep time (in minutes)
- Cook time (in minutes)
- Serving size (number of servings)
- Optional: difficulty level (easy, medium, hard)

CRITICAL INGREDIENT FORMAT:
Each ingredient MUST be an object with three fields:
- name: string - ONLY the ingredient name, NO measurements (e.g., "cream cheese", "garlic powder")
- quantity: number - MUST be a number (e.g., 8, 0.5, not "8" or "1/2")
- unit: string - measurement unit only (e.g., "oz", "cup", "tbsp", "tsp", "g", "ml")

CORRECT Examples:
  {"name": "cream cheese", "quantity": 8, "unit": "oz"}
  {"name": "garlic powder", "quantity": 0.5, "unit": "tsp"}
  {"name": "all-purpose flour", "quantity": 2, "unit": "cup"}

INCORRECT - DO NOT DO THIS:
  "8 oz cream cheese, softened" (string instead of object)
  {"name": "8 oz cream cheese", "quantity": 1, "unit": "serving"} (measurement in name)
  {"name": "1/2 tsp garlic powder", "quantity": 1, "unit": "serving"} (measurement in name)

IMPORTANT: The 'name' field should NEVER contain numbers or measurements!

RECIPE CATEGORIES:
When creating recipes, you MUST select the most appropriate category from these options:
- breakfast: Morning meals, brunch items (e.g., pancakes, eggs, oatmeal)
- lunch: Midday meals (e.g., sandwiches, salads, soups)
- dinner: Evening main courses (e.g., pasta, grilled meats, casseroles)
- snack: Light foods between meals (e.g., chips, crackers, fruit)
- dessert: Sweet treats and after-dinner items (e.g., cakes, cookies, ice cream, puddings)
- staple: Base ingredients or components used in other recipes (e.g., sauces, doughs, stocks)
- frozen: Recipes specifically designed for freezing (e.g., freezer meals, make-ahead items)

Choose the MOST SPECIFIC category that fits. For example:
- Lava cake, brownies, cookies → dessert (NOT dinner, even if served after dinner)
- Ice cream, panna cotta, tiramisu → dessert
- Pizza dough, tomato sauce, chicken stock → staple
- Eggs benedict, french toast → breakfast
- Burrito bowl, pasta salad → lunch or dinner (depending on portion size)

You can help with:
- Creating random recipes
- Meal-specific recipes (breakfast, lunch, dinner, snacks)
- Recipes with dietary restrictions (vegan, vegetarian, gluten-free, dairy-free, etc.)
- Copycat recipes of popular dishes
- Iterating on recipes based on user feedback

IMPORTANT: When you want to create or update a recipe, you MUST:
1. First present the complete recipe details to the user
2. Ask for their confirmation before proceeding
3. Only use the provided tools after getting explicit approval

NOTE: When recipes are created, the system will automatically search for and add an appropriate
image based on the recipe name, so you don't need to manually search for images.

Available tools:
- create_recipe: Create a new recipe in the database (use only after user confirmation, images are added automatically)
- update_recipe: Update an existing recipe (use only after user confirmation)
- list_user_recipes: Get a list of the user's existing recipes for reference
- search_web: Search the internet for recipe ideas, cooking techniques, and ingredient information
- fetch_url: Retrieve content from a specific URL (useful when user shares a recipe link)
- search_images: Search for food/recipe images (optional, useful if you want to show image options to the user)

Always be conversational and helpful. If the user's request is unclear, ask clarifying questions."""

        # Append tags context
        full_prompt = base_prompt + tags_context

        # Append dietary preferences if available
        if dietary_context:
            full_prompt += dietary_context

        return full_prompt

    async def _get_tags_context(self, user: User) -> str:
        """Get context about available tags for the AI.

        Args:
            user: The current user

        Returns:
            String containing tag examples and guidance
        """
        # Get user's group IDs
        group_result = await self.db.execute(
            select(GroupMember.group_id).where(GroupMember.user_id == user.id)
        )
        user_group_ids = [row[0] for row in group_result.all()]

        # Get popular tags from accessible recipes
        result = await self.db.execute(
            select(
                RecipeTag.tag_name, RecipeTag.tag_category, func.count(RecipeTag.id).label("count")
            )
            .join(Recipe, Recipe.id == RecipeTag.recipe_id)
            .where(
                Recipe.deleted_at.is_(None),
                or_(
                    Recipe.owner_id == user.id,
                    Recipe.visibility == "public",
                    (Recipe.visibility == "group") & (Recipe.group_id.in_(user_group_ids)),
                ),
            )
            .group_by(RecipeTag.tag_name, RecipeTag.tag_category)
            .order_by(func.count(RecipeTag.id).desc())
            .limit(50)  # Get top 50 most used tags
        )

        tags_data = result.all()

        if not tags_data:
            return """

RECIPE TAGS:
When creating recipes, you should include relevant tags to help categorize and search for recipes.
Tags can include dietary restrictions, cuisine types, meal types, cooking methods, etc.

Common tag examples:
- Dietary: vegan, vegetarian, gluten-free, dairy-free, keto, paleo, low-carb, high-protein
- Cuisine: italian, mexican, chinese, indian, thai, french, japanese, mediterranean
- Meal Type: breakfast, lunch, dinner, snack, dessert, appetizer
- Cooking Method: baking, grilling, slow-cooker, instant-pot, no-cook, one-pot
- Occasion: holiday, party, quick-meal, meal-prep, comfort-food

Always include relevant tags in the 'tags' array when creating or updating recipes.
"""

        # Group tags by category
        tags_by_category = {}
        for tag_name, tag_category, count in tags_data:
            category = tag_category or "other"
            if category not in tags_by_category:
                tags_by_category[category] = []
            tags_by_category[category].append(tag_name)

        # Build context string
        context = """

RECIPE TAGS:
When creating recipes, you should include relevant tags to help categorize and search for recipes.
Here are tags that are already being used in this system:

"""
        for category, tags in tags_by_category.items():
            context += (
                f"\n{category.upper()}: {', '.join(tags[:15])}"  # Limit to 15 tags per category
            )

        context += """

Feel free to use these existing tags or create new ones that are relevant.
Always include relevant tags in the 'tags' array when creating or updating recipes.
"""

        return context

    async def _get_dietary_preferences_context(
        self, user: User, use_dietary_preferences: bool = True
    ) -> str:
        """Get context about user's dietary preferences if enabled.

        Args:
            user: The current user
            use_dietary_preferences: Whether to use dietary preferences for this request

        Returns:
            String containing dietary preferences or empty string if disabled
        """
        # Check if user has enabled dietary preferences in AI and this request wants to use them
        if use_dietary_preferences and user.dietary_preferences is not None and user.dietary_preferences:
            prefs = ", ".join(user.dietary_preferences)
            dietary_text = """

USER DIETARY PREFERENCES:
The user has the following dietary preferences: {preferences}

IMPORTANT: Unless the user explicitly requests otherwise, all recipes you create should
comply with these dietary preferences. You should mention in your response that you're
taking their preferences into account. If a user asks for a recipe that conflicts with
their preferences (e.g., a vegan user asks for a steak recipe), confirm with them first
before proceeding.
"""
            return dietary_text.format(preferences=prefs)

        return """

NOTE: This user has not set any dietary preferences, or has chosen not to use them for this request.
Create recipes based solely on their requests without dietary restrictions.
"""

    def get_tools_definition(self) -> list[dict[str, Any]]:
        """Get the tools/functions definition for OpenAI function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_recipe",
                    "description": "Create a new recipe in the database. ONLY use this after the user has confirmed the recipe details.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "The name of the recipe"},
                            "description": {
                                "type": "string",
                                "description": "A brief description of the recipe",
                            },
                            "ingredients": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "Ingredient name",
                                        },
                                        "quantity": {
                                            "type": "number",
                                            "description": "Amount of ingredient",
                                        },
                                        "unit": {
                                            "type": "string",
                                            "description": "Unit of measurement (e.g., cup, tbsp, oz, g)",
                                        },
                                    },
                                    "required": ["name", "quantity", "unit"],
                                },
                                "description": "List of ingredients with name, quantity, and unit",
                            },
                            "instructions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Step-by-step cooking instructions",
                            },
                            "prep_time": {
                                "type": "integer",
                                "description": "Preparation time in minutes",
                            },
                            "cook_time": {
                                "type": "integer",
                                "description": "Cooking time in minutes",
                            },
                            "servings": {"type": "integer", "description": "Number of servings"},
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Recipe tags (e.g., vegan, gluten-free, etc.)",
                            },
                            "difficulty": {
                                "type": "string",
                                "enum": ["easy", "medium", "hard"],
                                "description": "Recipe difficulty level",
                            },
                            "category": {
                                "type": "string",
                                "enum": [
                                    "breakfast",
                                    "lunch",
                                    "dinner",
                                    "snack",
                                    "dessert",
                                    "staple",
                                    "frozen",
                                ],
                                "description": "Recipe category - choose the most appropriate meal type or category",
                            },
                            "cuisine": {
                                "type": "string",
                                "description": "Cuisine type (e.g., Italian, Mexican, etc.)",
                            },
                            "image_url": {
                                "type": "string",
                                "description": "URL of the recipe image. Should be obtained by calling search_images first.",
                            },
                        },
                        "required": [
                            "name",
                            "ingredients",
                            "instructions",
                            "prep_time",
                            "cook_time",
                            "servings",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_recipe",
                    "description": "Update an existing recipe. ONLY use this after the user has confirmed the changes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recipe_id": {
                                "type": "integer",
                                "description": "The ID of the recipe to update",
                            },
                            "name": {
                                "type": "string",
                                "description": "The updated name of the recipe",
                            },
                            "description": {
                                "type": "string",
                                "description": "The updated description",
                            },
                            "ingredients": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "Ingredient name",
                                        },
                                        "quantity": {
                                            "type": "number",
                                            "description": "Amount of ingredient",
                                        },
                                        "unit": {
                                            "type": "string",
                                            "description": "Unit of measurement",
                                        },
                                    },
                                    "required": ["name", "quantity", "unit"],
                                },
                                "description": "Updated list of ingredients with name, quantity, and unit",
                            },
                            "instructions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Updated instructions",
                            },
                            "prep_time": {
                                "type": "integer",
                                "description": "Updated prep time in minutes",
                            },
                            "cook_time": {
                                "type": "integer",
                                "description": "Updated cook time in minutes",
                            },
                            "servings": {
                                "type": "integer",
                                "description": "Updated number of servings",
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Updated tags",
                            },
                            "difficulty": {
                                "type": "string",
                                "enum": ["easy", "medium", "hard"],
                                "description": "Updated difficulty level",
                            },
                            "cuisine": {"type": "string", "description": "Updated cuisine type"},
                        },
                        "required": ["recipe_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_user_recipes",
                    "description": "Get a list of the user's existing recipes. Useful for referencing or updating recipes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of recipes to return",
                                "default": 10,
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the internet for recipes, cooking techniques, ingredient information, or culinary knowledge. Returns search results with titles, URLs, and snippets.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query"},
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 5)",
                                "default": 5,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fetch_url",
                    "description": "Fetch and extract text content from a specific URL. Useful when the user provides a recipe link or wants to import a recipe from a website.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to fetch content from",
                            }
                        },
                        "required": ["url"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_images",
                    "description": "Search for food/recipe images. Returns a list of image URLs that can be suggested to the user for their recipe.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query for images (e.g., 'chocolate cake', 'pasta carbonara')",
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of image results to return (default: 5)",
                                "default": 5,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

    async def chat(
        self, messages: list[dict[str, str]], user: User, use_dietary_preferences: bool = True
    ) -> dict[str, Any]:
        """
        Send a chat message to OpenAI and get a response.

        Args:
            messages: List of chat messages with 'role' and 'content'
            user: The current user
            use_dietary_preferences: Whether to use dietary preferences for this request

        Returns:
            dict with 'message' (str) and optional 'tool_calls' (list)
        """
        if not self.client:
            await self.initialize()

        # Prepend system message with user context
        system_prompt = await self.get_system_prompt(user, use_dietary_preferences)
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        logger.info(
            f"Sending chat request with {len(messages)} user messages, use_dietary_preferences={use_dietary_preferences}"
        )
        logger.debug(
            f"Last user message: {messages[-1]['content'][:200] if messages else 'No messages'}"
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.settings.model if self.settings else "gpt-4",
                messages=full_messages,
                tools=self.get_tools_definition(),
            )

            message = response.choices[0].message
            logger.debug(f"AI response content length: {len(message.content or '')}")

            result: dict[str, Any] = {
                "message": message.content or "",
            }

            # Check if there are tool calls
            if message.tool_calls:
                tool_calls = []
                for tool_call in message.tool_calls:
                    tool_data = {
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments),
                    }
                    tool_calls.append(tool_data)
                    logger.info(f"AI requested tool: {tool_call.function.name}")
                    logger.debug(f"Tool arguments: {json.dumps(tool_data['arguments'], indent=2)}")
                result["tool_calls"] = tool_calls

            return result

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
            raise ValueError(f"OpenAI API error: {str(e)}")

    async def create_recipe(self, recipe_data: dict[str, Any], user: User) -> Recipe:
        """Create a new recipe from AI-generated data.

        Args:
            recipe_data: Recipe data from AI function call
            user: The current user

        Returns:
            The created Recipe object
        """
        logger.info(f"Creating recipe: {recipe_data.get('name', 'Unknown')}")
        logger.debug(f"Recipe data: {json.dumps(recipe_data, indent=2)}")

        # Validate and clean ingredients
        ingredients = recipe_data.get("ingredients", [])
        cleaned_ingredients = []

        for idx, ing in enumerate(ingredients):
            if not isinstance(ing, dict):
                raise ValueError(
                    f"Ingredient {idx + 1} must be an object with name, quantity, and unit"
                )

            name = ing.get("name", "").strip()
            quantity = ing.get("quantity")
            unit = ing.get("unit", "").strip()

            # Validate ingredient has all required fields
            if not name:
                raise ValueError(f"Ingredient {idx + 1} must have a name")
            if quantity is None or not isinstance(quantity, (int, float)):
                raise ValueError(f"Ingredient '{name}' must have a numeric quantity")
            if not unit:
                raise ValueError(f"Ingredient '{name}' must have a unit")

            # Check if name contains measurements (common AI error)
            if name and (name[0].isdigit() or name.startswith("(")):
                raise ValueError(
                    f"Ingredient '{name}' appears to contain measurements in the name field. "
                    "Measurements should only be in quantity and unit fields."
                )

            cleaned_ingredients.append({"name": name, "quantity": float(quantity), "unit": unit})

        # Use image_url from recipe_data if provided, otherwise search for one
        image_url = recipe_data.get("image_url")
        if not image_url:
            # Automatically search for an image based on the recipe name
            recipe_name = recipe_data["name"]
            logger.info(f"No image provided, searching for '{recipe_name}' images")
            try:
                image_results = await self.search_images(recipe_name, max_results=1)
                if image_results and len(image_results) > 0:
                    image_url = image_results[0].get("url")
                    logger.info(f"Found image for recipe: {image_url}")
                else:
                    logger.warning(f"No images found for '{recipe_name}', using placeholder")
                    # Use placeholder image from configuration
                    image_url = settings.DEFAULT_RECIPE_IMAGE
                    if image_url and not image_url.startswith(("http://", "https://")):
                        image_url = f"{settings.BACKEND_URL}{image_url}"
            except Exception as e:
                logger.warning(f"Image search failed: {str(e)}, using placeholder")
                # Use placeholder image from configuration
                image_url = settings.DEFAULT_RECIPE_IMAGE
                if image_url and not image_url.startswith(("http://", "https://")):
                    image_url = f"{settings.BACKEND_URL}{image_url}"

        recipe = Recipe(
            owner_id=user.id,
            title=recipe_data["name"],
            description=recipe_data.get("description", ""),
            ingredients=cleaned_ingredients,
            instructions=recipe_data["instructions"],
            prep_time=recipe_data["prep_time"],
            cook_time=recipe_data["cook_time"],
            serving_size=recipe_data["servings"],
            difficulty=recipe_data.get("difficulty"),
            category=recipe_data.get("category"),  # Add category field
            visibility="private",  # Default to private
            image_url=image_url,
        )

        self.db.add(recipe)
        await self.db.commit()
        await self.db.refresh(recipe)

        # Add tags if provided
        tags = recipe_data.get("tags", [])
        if tags:
            for tag_name in tags:
                if tag_name and tag_name.strip():
                    # Determine tag category based on common patterns
                    tag_category = self._categorize_tag(tag_name.strip().lower())
                    recipe_tag = RecipeTag(
                        recipe_id=recipe.id,
                        tag_name=tag_name.strip().lower(),
                        tag_category=tag_category,
                    )
                    self.db.add(recipe_tag)

            await self.db.commit()
            await self.db.refresh(recipe)

        return recipe

    async def update_recipe(self, recipe_data: dict[str, Any], user: User) -> Recipe:
        """
        Update an existing recipe from AI-generated data.

        Args:
            recipe_data: Recipe data from AI function call (must include recipe_id)
            user: The current user

        Returns:
            The updated Recipe object
        """
        recipe_id = recipe_data.get("recipe_id")
        if not recipe_id:
            raise ValueError("recipe_id is required for updating a recipe")

        result = await self.db.execute(
            select(Recipe).where(
                Recipe.id == recipe_id, Recipe.owner_id == user.id, Recipe.deleted_at.is_(None)
            )
        )
        recipe = result.scalar_one_or_none()

        if not recipe:
            raise ValueError(
                f"Recipe with ID {recipe_id} not found or you don't have permission to edit it"
            )

        # Update fields that were provided
        update_fields = [
            "description",
            "ingredients",
            "instructions",
            "prep_time",
            "cook_time",
            "difficulty",
            "category",
        ]

        for field in update_fields:
            if field in recipe_data:
                setattr(recipe, field, recipe_data[field])

        # Handle mapped fields
        if "name" in recipe_data:
            recipe.title = recipe_data["name"]
        if "servings" in recipe_data:
            recipe.serving_size = recipe_data["servings"]

        # Update tags if provided
        if "tags" in recipe_data:
            # Delete existing tags
            await self.db.execute(
                RecipeTag.__table__.delete().where(RecipeTag.recipe_id == recipe_id)
            )

            # Add new tags
            tags = recipe_data.get("tags", [])
            for tag_name in tags:
                if tag_name and tag_name.strip():
                    tag_category = self._categorize_tag(tag_name.strip().lower())
                    recipe_tag = RecipeTag(
                        recipe_id=recipe.id,
                        tag_name=tag_name.strip().lower(),
                        tag_category=tag_category,
                    )
                    self.db.add(recipe_tag)

        await self.db.commit()
        await self.db.refresh(recipe)

        return recipe

    async def list_user_recipes(self, user: User, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get a list of user's recipes for the AI to reference.

        Args:
            user: The current user
            limit: Maximum number of recipes to return

        Returns:
            List of recipe dictionaries with basic info
        """
        result = await self.db.execute(
            select(Recipe)
            .where(Recipe.owner_id == user.id, Recipe.deleted_at.is_(None))
            .limit(limit)
        )
        recipes = result.scalars().all()

        return [
            {
                "id": recipe.id,
                "name": recipe.title,
                "description": recipe.description,
                "difficulty": recipe.difficulty,
            }
            for recipe in recipes
        ]

    def _categorize_tag(self, tag_name: str) -> str:
        """Categorize a tag based on its name.

        Args:
            tag_name: The tag name (lowercase)

        Returns:
            The category for this tag
        """
        dietary_tags = {
            "vegan",
            "vegetarian",
            "gluten-free",
            "dairy-free",
            "keto",
            "paleo",
            "low-carb",
            "high-protein",
            "nut-free",
            "egg-free",
            "soy-free",
            "sugar-free",
            "whole30",
            "pescatarian",
            "halal",
            "kosher",
        }

        cuisine_tags = {
            "italian",
            "mexican",
            "chinese",
            "indian",
            "thai",
            "french",
            "japanese",
            "mediterranean",
            "greek",
            "korean",
            "vietnamese",
            "spanish",
            "middle-eastern",
            "american",
            "cajun",
            "caribbean",
        }

        meal_type_tags = {
            "breakfast",
            "lunch",
            "dinner",
            "snack",
            "dessert",
            "appetizer",
            "side-dish",
            "main-course",
            "brunch",
            "beverage",
        }

        cooking_method_tags = {
            "baking",
            "grilling",
            "slow-cooker",
            "instant-pot",
            "no-cook",
            "one-pot",
            "air-fryer",
            "pressure-cooker",
            "stovetop",
            "roasting",
            "steaming",
            "frying",
            "sauteing",
        }

        if tag_name in dietary_tags:
            return "dietary"
        elif tag_name in cuisine_tags:
            return "cuisine"
        elif tag_name in meal_type_tags:
            return "meal_type"
        elif tag_name in cooking_method_tags:
            return "cooking_method"
        else:
            return "other"

    async def search_web(self, query: str, max_results: int = 5) -> list[dict[str, str]]:
        """
        Search the web using SEARXNG.

        Args:
            query: The search query
            max_results: Maximum number of results to return

        Returns:
            List of search results with title, url, and content
        """
        # Get SEARXNG URL from settings or use default
        searxng_url = getattr(self.settings, "searxng_url", None) or "http://localhost:8085"
        logger.info(
            f"Searching web with query: '{query}', max_results: {max_results}, searxng_url: {searxng_url}"
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{searxng_url}/search",
                    params={
                        "q": query,
                        "format": "json",
                        "categories": "general",
                    },
                )
                response.raise_for_status()
                data = response.json()

                logger.debug(f"Search returned {len(data.get('results', []))} results")

                results = []
                for result in data.get("results", [])[:max_results]:
                    results.append(
                        {
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "content": result.get("content", ""),
                        }
                    )

                logger.info(f"Returning {len(results)} search results")
                return results

        except Exception as e:
            logger.error(f"Search error: {str(e)}", exc_info=True)
            raise ValueError(f"Search error: {str(e)}")

    async def fetch_url(self, url: str) -> dict[str, str]:
        """
        Fetch and extract text content from a URL.

        Args:
            url: The URL to fetch

        Returns:
            Dict with title and text content
        """
        logger.info(f"Fetching URL: {url}")
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                logger.debug(f"Sending GET request to {url}")
                response = await client.get(
                    url, headers={"User-Agent": "Mozilla/5.0 (compatible; MealPlannerBot/1.0)"}
                )
                response.raise_for_status()

                logger.debug(
                    f"Response status: {response.status_code}, Content-Type: {response.headers.get('content-type')}"
                )
                logger.debug(f"Response length: {len(response.text)} characters")

                # Parse HTML
                if BeautifulSoup is None:
                    raise RuntimeError(
                        "beautifulsoup4 is required for fetch_url; install it to enable HTML parsing"
                    )
                soup = BeautifulSoup(response.text, "html.parser")

                # Get title
                title = soup.title.string if soup.title else "No title"
                logger.debug(f"Page title: {title}")

                # Try to find recipe-specific content first
                recipe_content = None

                # Look for common recipe schema.org markup
                recipe_schema = soup.find("script", type="application/ld+json")
                if recipe_schema:
                    try:
                        schema_data = json.loads(recipe_schema.string)
                        if isinstance(schema_data, dict) and schema_data.get("@type") == "Recipe":
                            logger.info("Found Recipe schema.org markup")
                            recipe_content = json.dumps(schema_data, indent=2)
                    except Exception:
                        # Ignore parsing errors but log them for debug
                        logger.debug(
                            "Failed to parse schema.org markup for recipe content", exc_info=True
                        )
                        pass

                # Look for article or main content
                if not recipe_content:
                    main_content = (
                        soup.find("article")
                        or soup.find("main")
                        or soup.find(
                            class_=lambda x: x and ("recipe" in x.lower() or "content" in x.lower())
                        )
                        or soup.find("body")
                    )

                    if main_content:
                        # Remove unwanted elements from main content
                        for unwanted in main_content.find_all(
                            ["script", "style", "nav", "footer", "aside", "iframe", "noscript"]
                        ):
                            unwanted.decompose()

                        # Get text from main content
                        recipe_content = main_content.get_text(separator="\n", strip=True)

                # Fallback to full page text
                if not recipe_content:
                    logger.debug("Using full page text extraction")
                    # Remove unwanted elements
                    for script in soup(
                        [
                            "script",
                            "style",
                            "nav",
                            "footer",
                            "header",
                            "aside",
                            "iframe",
                            "noscript",
                        ]
                    ):
                        script.decompose()

                    recipe_content = soup.get_text(separator="\n", strip=True)

                # Clean up text (remove excessive newlines and whitespace)
                lines = [line.strip() for line in recipe_content.split("\n") if line.strip()]
                cleaned_text = "\n".join(lines)

                logger.debug(f"Extracted text length: {len(cleaned_text)} characters")
                logger.debug(f"First 1000 chars:\n{cleaned_text[:1000]}")

                # Limit content to avoid token limits (first 10000 characters for better context)
                if len(cleaned_text) > 10000:
                    logger.debug("Content truncated at 10000 characters")
                    cleaned_text = cleaned_text[:10000] + "\n\n... [content truncated for length]"

                result = {"title": title, "url": url, "content": cleaned_text}

                logger.info(f"Successfully fetched URL: {url}, content length: {len(cleaned_text)}")
                return result

        except Exception as e:
            logger.error(f"Failed to fetch URL {url}: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to fetch URL: {str(e)}")

    async def search_images(self, query: str, max_results: int = 5) -> list[dict[str, str]]:
        """
        Search for images using SEARXNG.

        Args:
            query: The search query for images
            max_results: Maximum number of image results to return

        Returns:
            List of image results with url, thumbnail, title, and source
        """
        # Get SEARXNG URL from settings or use default
        searxng_url = getattr(self.settings, "searxng_url", None) or "http://localhost:8085"
        logger.info(
            f"Searching images with query: '{query}', max_results: {max_results}, searxng_url: {searxng_url}"
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{searxng_url}/search",
                    params={
                        "q": query,
                        "format": "json",
                        "categories": "images",
                    },
                )
                response.raise_for_status()
                data = response.json()

                logger.debug(f"Image search returned {len(data.get('results', []))} results")

                results = []
                for result in data.get("results", [])[:max_results]:
                    results.append(
                        {
                            "url": result.get("img_src", ""),
                            "thumbnail": result.get("thumbnail_src", result.get("img_src", "")),
                            "title": result.get("title", ""),
                            "source": result.get("url", ""),
                            "width": result.get("img_width"),
                            "height": result.get("img_height"),
                        }
                    )

                logger.info(f"Returning {len(results)} image results")
                return results

        except Exception as e:
            logger.error(f"Image search error: {str(e)}", exc_info=True)
            raise ValueError(f"Image search error: {str(e)}")
