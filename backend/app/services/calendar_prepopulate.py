"""Calendar prepopulation service."""

import logging
import random
from datetime import datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CalendarMeal,
    GroupMember,
    Recipe,
    RecipeCollection,
    RecipeCollectionItem,
    RecipeTag,
    User,
)

logger = logging.getLogger(__name__)


class CalendarPrepopulateService:
    """Service for prepopulating calendars with meals."""

    def __init__(self, db: AsyncSession):
        """Initialize the service."""
        self.db = db

    async def prepopulate_calendar(
        self,
        calendar_id: int,
        user: User,
        start_date: datetime,
        period: str,
        meal_types: list[str],
        snacks_per_day: int = 0,
        desserts_per_day: int = 0,
        use_dietary_preferences: bool = True,
        avoid_duplicates: bool = True,
        collection_id: int | None = None,
    ) -> tuple[int, datetime]:
        """
        Prepopulate a calendar with meals.

        Args:
            calendar_id: The calendar to prepopulate
            user: The user making the request
            start_date: Starting date for prepopulation
            period: Time period (day, week, month)
            meal_types: List of meal types to include (breakfast, lunch, dinner)
            snacks_per_day: Number of snacks to add per day
            desserts_per_day: Number of desserts to add per day
            use_dietary_preferences: Whether to filter by dietary preferences
            avoid_duplicates: Try to avoid duplicate recipes
            collection_id: Optional collection ID to limit recipes to collection

        Returns:
            Tuple of (number of meals created, end date)
        """
        logger.info(
            "Prepopulating calendar: calendar_id=%s, period=%s, meal_types=%s, use_dietary=%s, collection_id=%s",
            calendar_id, period, meal_types, use_dietary_preferences, collection_id
        )
        # Calculate end date based on period
        if period == "day":
            end_date = start_date
        elif period == "week":
            end_date = start_date + timedelta(days=6)
        elif period == "month":
            # Approximate month as 30 days
            end_date = start_date + timedelta(days=29)
        else:
            logger.error("Invalid period specified: %s", period)
            raise ValueError(f"Invalid period: {period}")

        # Get available recipes for each category
        recipes_by_category = {}

        # Get regular meal recipes
        for meal_type in meal_types:
            recipes = await self._get_recipes_for_category(
                user, meal_type, use_dietary_preferences, collection_id
            )
            recipes_by_category[meal_type] = recipes
            logger.debug("Found %d recipes for meal_type=%s", len(recipes), meal_type)

        # Get snack recipes if needed
        if snacks_per_day > 0:
            snack_recipes = await self._get_recipes_for_category(
                user, "snack", use_dietary_preferences, collection_id
            )
            recipes_by_category["snack"] = snack_recipes

        # Get dessert recipes if needed
        if desserts_per_day > 0:
            dessert_recipes = await self._get_recipes_for_category(
                user, "dessert", use_dietary_preferences, collection_id
            )
            recipes_by_category["dessert"] = dessert_recipes

        # Check if we have enough recipes
        for category, recipes in recipes_by_category.items():
            if not recipes:
                raise ValueError(
                    f"No recipes found for category '{category}'. Please add some recipes first."
                )

        # Generate meal plan
        meals_created = 0
        current_date = start_date
        used_recipe_ids = set() if avoid_duplicates else None

        while current_date <= end_date:
            # Add regular meals
            for meal_type in meal_types:
                recipe = self._select_recipe(
                    recipes_by_category[meal_type], used_recipe_ids, avoid_duplicates
                )
                if recipe:
                    await self._create_meal(calendar_id, int(recipe.id), current_date, meal_type)
                    meals_created += 1

            # Add snacks
            for _ in range(snacks_per_day):
                if "snack" in recipes_by_category:
                    recipe = self._select_recipe(
                        recipes_by_category["snack"], used_recipe_ids, avoid_duplicates
                    )
                    if recipe:
                        await self._create_meal(calendar_id, int(recipe.id), current_date, "snack")
                        meals_created += 1

            # Add desserts (as snack type since dessert is a category, not meal type)
            for _ in range(desserts_per_day):
                if "dessert" in recipes_by_category:
                    recipe = self._select_recipe(
                        recipes_by_category["dessert"], used_recipe_ids, avoid_duplicates
                    )
                    if recipe:
                        await self._create_meal(calendar_id, int(recipe.id), current_date, "snack")
                        meals_created += 1

            current_date += timedelta(days=1)

        await self.db.commit()
        return meals_created, end_date

    async def _get_recipes_for_category(
        self,
        user: User,
        category: str,
        use_dietary_preferences: bool,
        collection_id: int | None = None,
    ) -> list[Recipe]:
        """
        Get recipes for a specific category.

        Args:
            user: The user making the request
            category: The recipe category
            use_dietary_preferences: Whether to filter by dietary preferences
            collection_id: Optional collection ID to limit recipes to collection

        Returns:
            List of recipes
        """
        # Get user's group IDs
        group_result = await self.db.execute(
            select(GroupMember.group_id).where(GroupMember.user_id == user.id)
        )
        user_group_ids = [row[0] for row in group_result.all()]

        # If collection_id is provided, get recipes from that collection
        if collection_id is not None:
            # Verify collection exists and user has access
            coll_result = await self.db.execute(
                select(RecipeCollection).where(RecipeCollection.id == collection_id)
            )
            collection = coll_result.scalar_one_or_none()
            if not collection or collection.user_id != user.id:
                logger.warning(
                    "User %s tried to access collection %s they don't own",
                    user.id,
                    collection_id,
                )
                raise ValueError(f"Collection {collection_id} not found or not accessible")

            # Get recipe IDs from collection that match the category
            items_result = await self.db.execute(
                select(RecipeCollectionItem.recipe_id).where(
                    RecipeCollectionItem.collection_id == collection_id
                )
            )
            collection_recipe_ids = [row[0] for row in items_result.all()]

            # Build query for recipes in collection with matching category
            query = select(Recipe).where(
                Recipe.id.in_(collection_recipe_ids),
                Recipe.category == category,
                Recipe.deleted_at.is_(None),
            )
        else:
            # Build query for accessible recipes
            query = select(Recipe).where(
                Recipe.deleted_at.is_(None),
                Recipe.category == category,
                or_(
                    Recipe.owner_id == user.id,  # User's own recipes
                    Recipe.visibility == "public",  # Public recipes
                    (Recipe.visibility == "group")
                    & (Recipe.group_id.in_(user_group_ids)),  # Group recipes
                ),
            )

        # Filter by dietary preferences if requested
        if use_dietary_preferences and user.dietary_preferences:
            # Get recipes that have tags matching dietary preferences
            dietary_prefs = (
                user.dietary_preferences if isinstance(user.dietary_preferences, list) else []
            )
            if dietary_prefs:
                # Join with RecipeTag to filter
                query = (
                    query.join(RecipeTag, RecipeTag.recipe_id == Recipe.id)
                    .where(RecipeTag.tag_name.in_(dietary_prefs))
                    .distinct()
                )

        result = await self.db.execute(query)
        recipes = result.scalars().all()
        return list(recipes)

    def _select_recipe(
        self,
        recipes: list[Recipe],
        used_recipe_ids: set | None,
        avoid_duplicates: bool,
    ) -> Recipe | None:
        """
        Select a recipe from the list.

        Args:
            recipes: List of available recipes
            used_recipe_ids: Set of already used recipe IDs
            avoid_duplicates: Whether to avoid duplicates

        Returns:
            Selected recipe or None if no recipes available
        """
        if not recipes:
            return None

        # Filter out used recipes if avoiding duplicates
        if avoid_duplicates and used_recipe_ids:
            available_recipes = [r for r in recipes if r.id not in used_recipe_ids]
            # If no unused recipes, fall back to all recipes
            if not available_recipes:
                available_recipes = recipes
        else:
            available_recipes = recipes

        # Randomly select a recipe
        recipe = random.choice(available_recipes)

        # Mark as used if avoiding duplicates
        if avoid_duplicates and used_recipe_ids is not None:
            used_recipe_ids.add(int(recipe.id))

        return recipe

    async def _create_meal(
        self,
        calendar_id: int,
        recipe_id: int,
        meal_date: datetime,
        meal_type: str,
    ) -> None:
        """
        Create a calendar meal entry.

        Args:
            calendar_id: The calendar ID
            recipe_id: The recipe ID
            meal_date: The date for the meal
            meal_type: The type of meal
        """
        # Convert timezone-aware datetime to naive (UTC) for storage
        meal_date_naive = meal_date.replace(tzinfo=None) if meal_date.tzinfo else meal_date

        meal = CalendarMeal(
            calendar_id=calendar_id,
            recipe_id=recipe_id,
            meal_date=meal_date_naive,
            meal_type=meal_type,
        )
        self.db.add(meal)
