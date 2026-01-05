"""Add tags to existing recipes."""

import asyncio
import sys
from pathlib import Path

# Add backend root directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Recipe, RecipeTag


async def add_tags():
    """Add tags to existing recipes."""
    print("🏷️  Adding tags to recipes...")
    print("=" * 50)

    async with AsyncSessionLocal() as db:  # type: ignore
        try:
            # Get all recipes
            result = await db.execute(select(Recipe).where(Recipe.deleted_at.is_(None)))
            recipes = list(result.scalars().all())

            if not recipes:
                print("No recipes found in database!")
                return

            print(f"Found {len(recipes)} recipes")

            # Define tags for common recipe types
            tag_mapping = {
                "carbonara": [
                    {"tag_name": "Italian", "tag_category": "cuisine"},
                    {"tag_name": "Pasta", "tag_category": "main_ingredient"},
                    {"tag_name": "Comfort Food", "tag_category": "meal_type"},
                ],
                "oat": [
                    {"tag_name": "Healthy", "tag_category": "dietary"},
                    {"tag_name": "No-Cook", "tag_category": "cooking_method"},
                    {"tag_name": "Make-Ahead", "tag_category": "meal_type"},
                    {"tag_name": "Vegetarian", "tag_category": "dietary"},
                ],
                "caesar": [
                    {"tag_name": "Salad", "tag_category": "meal_type"},
                    {"tag_name": "Chicken", "tag_category": "main_ingredient"},
                    {"tag_name": "Low-Carb", "tag_category": "dietary"},
                    {"tag_name": "Grilled", "tag_category": "cooking_method"},
                ],
                "pizza": [
                    {"tag_name": "Italian", "tag_category": "cuisine"},
                    {"tag_name": "Pizza", "tag_category": "meal_type"},
                    {"tag_name": "Vegetarian", "tag_category": "dietary"},
                    {"tag_name": "Baked", "tag_category": "cooking_method"},
                ],
                "curry": [
                    {"tag_name": "Thai", "tag_category": "cuisine"},
                    {"tag_name": "Spicy", "tag_category": "flavor"},
                    {"tag_name": "Curry", "tag_category": "meal_type"},
                    {"tag_name": "Chicken", "tag_category": "main_ingredient"},
                ],
                "taco": [
                    {"tag_name": "Mexican", "tag_category": "cuisine"},
                    {"tag_name": "Beef", "tag_category": "main_ingredient"},
                    {"tag_name": "Quick", "tag_category": "cooking_method"},
                    {"tag_name": "Family-Friendly", "tag_category": "meal_type"},
                ],
            }

            tags_created = 0

            for recipe in recipes:
                # Skip if recipe already has tags
                existing_tags_result = await db.execute(
                    select(RecipeTag).where(RecipeTag.recipe_id == recipe.id)
                )
                existing_tags = list(existing_tags_result.scalars().all())
                if existing_tags:
                    print(f"  ⏭️  Skipping {recipe.title} (already has {len(existing_tags)} tags)")
                    continue

                # Find matching tags
                recipe_title_lower = recipe.title.lower()
                tags_to_add = []

                for keyword, tags in tag_mapping.items():
                    if keyword in recipe_title_lower:
                        tags_to_add = tags
                        break

                # Add default tags for recipes without specific matches
                if not tags_to_add:
                    tags_to_add = [
                        {"tag_name": "Homemade", "tag_category": "meal_type"},
                    ]
                    # Add category-based tags
                    if recipe.category:
                        tags_to_add.append(
                            {"tag_name": recipe.category.capitalize(), "tag_category": "meal_type"}
                        )
                    # Add difficulty tag
                    if recipe.difficulty:
                        tags_to_add.append(
                            {
                                "tag_name": recipe.difficulty.capitalize(),
                                "tag_category": "difficulty",
                            }
                        )

                # Create tags
                for tag_data in tags_to_add:
                    tag = RecipeTag(
                        recipe_id=recipe.id,
                        tag_name=tag_data["tag_name"],
                        tag_category=tag_data["tag_category"],
                    )
                    db.add(tag)
                    tags_created += 1

                print(f"  ✅ Added {len(tags_to_add)} tags to '{recipe.title}'")

            await db.commit()
            print("=" * 50)
            print(f"✨ Successfully added {tags_created} tags to recipes!")

        except Exception as e:
            print(f"❌ Error adding tags: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(add_tags())
