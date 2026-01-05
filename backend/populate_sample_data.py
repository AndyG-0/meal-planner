"""Populate database with sample data for testing."""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Calendar, CalendarMeal, Group, GroupMember, Recipe, RecipeTag, User
from app.utils.auth import get_password_hash


async def create_sample_users(db: AsyncSession) -> list[User]:
    """Create sample users."""
    users = [
        User(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            is_admin=True,
        ),
        User(
            username="demo",
            email="demo@example.com",
            password_hash=get_password_hash("password123"),
            is_admin=False,
        ),
        User(
            username="chef_alice",
            email="alice@example.com",
            password_hash=get_password_hash("password123"),
            is_admin=False,
        ),
        User(
            username="foodie_bob",
            email="bob@example.com",
            password_hash=get_password_hash("password123"),
            is_admin=False,
        ),
    ]

    for user in users:
        db.add(user)

    await db.commit()
    for user in users:
        await db.refresh(user)

    print(f"✅ Created {len(users)} sample users")
    return users


async def create_sample_groups(db: AsyncSession, users: list[User]) -> list[Group]:
    """Create sample groups."""
    # Create a family group with demo user as owner
    family_group = Group(
        name="Family Recipes",
        owner_id=users[1].id,  # demo user
    )
    db.add(family_group)
    await db.commit()
    await db.refresh(family_group)

    # Add chef_alice and foodie_bob as members
    members = [
        GroupMember(
            group_id=family_group.id,
            user_id=users[2].id,  # chef_alice
            role="admin",
        ),
        GroupMember(
            group_id=family_group.id,
            user_id=users[3].id,  # foodie_bob
            role="member",
        ),
    ]

    for member in members:
        db.add(member)

    await db.commit()
    print(f"✅ Created sample group with {len(members)} members")
    return [family_group]


async def create_sample_recipes(
    db: AsyncSession, users: list[User], groups: list[Group]
) -> list[Recipe]:
    """Create sample recipes."""
    recipes_data = [
        {
            "title": "Classic Spaghetti Carbonara",
            "description": "A traditional Italian pasta dish with eggs, cheese, pancetta, and black pepper",
            "ingredients": [
                {"name": "Spaghetti", "quantity": 400, "unit": "g"},
                {"name": "Pancetta", "quantity": 200, "unit": "g"},
                {"name": "Eggs", "quantity": 4, "unit": "whole"},
                {"name": "Parmesan cheese", "quantity": 100, "unit": "g"},
                {"name": "Black pepper", "quantity": 1, "unit": "tsp"},
            ],
            "instructions": [
                "Cook spaghetti in salted boiling water until al dente",
                "Fry pancetta until crispy",
                "Beat eggs with grated parmesan and black pepper",
                "Drain pasta, reserve some pasta water",
                "Mix hot pasta with pancetta, then remove from heat",
                "Add egg mixture quickly while tossing to create creamy sauce",
                "Add pasta water if needed to reach desired consistency",
                "Serve immediately with extra parmesan",
            ],
            "serving_size": 4,
            "prep_time": 10,
            "cook_time": 20,
            "difficulty": "medium",
            "nutritional_info": {
                "calories": 520,
                "protein": 24,
                "carbs": 58,
                "fat": 22,
            },
            "image_url": "https://images.unsplash.com/photo-1612874742237-6526221588e3",
            "visibility": "public",
        },
        {
            "title": "Overnight Oats",
            "description": "Healthy and easy no-cook breakfast with oats, milk, and toppings",
            "ingredients": [
                {"name": "Rolled oats", "quantity": 0.5, "unit": "cup"},
                {"name": "Milk", "quantity": 0.5, "unit": "cup"},
                {"name": "Greek yogurt", "quantity": 0.25, "unit": "cup"},
                {"name": "Honey", "quantity": 1, "unit": "tbsp"},
                {"name": "Chia seeds", "quantity": 1, "unit": "tbsp"},
                {"name": "Berries", "quantity": 0.5, "unit": "cup"},
                {"name": "Banana", "quantity": 1, "unit": "whole"},
            ],
            "instructions": [
                "Mix oats, milk, yogurt, honey, and chia seeds in a jar",
                "Stir well to combine",
                "Cover and refrigerate overnight",
                "In the morning, top with fresh berries and sliced banana",
                "Add extra milk if too thick",
                "Enjoy cold",
            ],
            "serving_size": 1,
            "prep_time": 5,
            "cook_time": 0,
            "difficulty": "easy",
            "nutritional_info": {
                "calories": 350,
                "protein": 15,
                "carbs": 55,
                "fat": 8,
            },
            "image_url": "https://images.unsplash.com/photo-1517673400267-0251440c45dc",
            "visibility": "public",
        },
        {
            "title": "Grilled Chicken Caesar Salad",
            "description": "Fresh romaine lettuce with grilled chicken, parmesan, and classic Caesar dressing",
            "ingredients": [
                {"name": "Chicken breast", "quantity": 2, "unit": "pieces"},
                {"name": "Romaine lettuce", "quantity": 1, "unit": "head"},
                {"name": "Parmesan cheese", "quantity": 50, "unit": "g"},
                {"name": "Caesar dressing", "quantity": 4, "unit": "tbsp"},
                {"name": "Croutons", "quantity": 1, "unit": "cup"},
                {"name": "Olive oil", "quantity": 2, "unit": "tbsp"},
                {"name": "Lemon juice", "quantity": 1, "unit": "tbsp"},
            ],
            "instructions": [
                "Season chicken with salt, pepper, and olive oil",
                "Grill chicken for 6-7 minutes per side until cooked through",
                "Let chicken rest for 5 minutes, then slice",
                "Wash and chop romaine lettuce",
                "Toss lettuce with Caesar dressing",
                "Top with grilled chicken, parmesan shavings, and croutons",
                "Drizzle with lemon juice",
                "Serve immediately",
            ],
            "serving_size": 2,
            "prep_time": 15,
            "cook_time": 15,
            "difficulty": "easy",
            "nutritional_info": {
                "calories": 420,
                "protein": 38,
                "carbs": 12,
                "fat": 25,
            },
            "image_url": "https://images.unsplash.com/photo-1546793665-c74683f339c1",
            "visibility": "group",
            "group_id": None,  # Will be set dynamically
        },
        {
            "title": "Homemade Margherita Pizza",
            "description": "Classic Italian pizza with tomato sauce, mozzarella, and fresh basil",
            "ingredients": [
                {"name": "Pizza dough", "quantity": 500, "unit": "g"},
                {"name": "Tomato sauce", "quantity": 200, "unit": "ml"},
                {"name": "Fresh mozzarella", "quantity": 250, "unit": "g"},
                {"name": "Fresh basil", "quantity": 1, "unit": "bunch"},
                {"name": "Olive oil", "quantity": 2, "unit": "tbsp"},
                {"name": "Garlic", "quantity": 2, "unit": "cloves"},
                {"name": "Salt", "quantity": 1, "unit": "tsp"},
            ],
            "instructions": [
                "Preheat oven to 475°F (245°C) with pizza stone if available",
                "Roll out pizza dough into desired shape",
                "Spread tomato sauce evenly over dough",
                "Tear mozzarella and distribute over sauce",
                "Drizzle with olive oil and season with salt",
                "Bake for 12-15 minutes until crust is golden and cheese is bubbly",
                "Remove from oven and top with fresh basil leaves",
                "Slice and serve hot",
            ],
            "serving_size": 4,
            "prep_time": 20,
            "cook_time": 15,
            "difficulty": "medium",
            "nutritional_info": {
                "calories": 320,
                "protein": 14,
                "carbs": 42,
                "fat": 12,
            },
            "image_url": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002",
            "visibility": "public",
        },
        {
            "title": "Thai Green Curry",
            "description": "Aromatic and spicy coconut curry with vegetables and chicken",
            "ingredients": [
                {"name": "Chicken thigh", "quantity": 500, "unit": "g"},
                {"name": "Green curry paste", "quantity": 3, "unit": "tbsp"},
                {"name": "Coconut milk", "quantity": 400, "unit": "ml"},
                {"name": "Bell peppers", "quantity": 2, "unit": "whole"},
                {"name": "Bamboo shoots", "quantity": 1, "unit": "cup"},
                {"name": "Thai basil", "quantity": 1, "unit": "cup"},
                {"name": "Fish sauce", "quantity": 2, "unit": "tbsp"},
                {"name": "Brown sugar", "quantity": 1, "unit": "tbsp"},
            ],
            "instructions": [
                "Heat oil in a large pan or wok",
                "Fry curry paste for 1-2 minutes until fragrant",
                "Add chicken and cook until no longer pink",
                "Pour in coconut milk and bring to simmer",
                "Add vegetables and cook for 10 minutes",
                "Season with fish sauce and sugar",
                "Add Thai basil just before serving",
                "Serve with jasmine rice",
            ],
            "serving_size": 4,
            "prep_time": 15,
            "cook_time": 25,
            "difficulty": "medium",
            "nutritional_info": {
                "calories": 380,
                "protein": 28,
                "carbs": 15,
                "fat": 24,
            },
            "image_url": "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd",
            "visibility": "private",
        },
        {
            "title": "Chocolate Chip Cookies",
            "description": "Classic homemade cookies with chocolate chips",
            "ingredients": [
                {"name": "All-purpose flour", "quantity": 2.25, "unit": "cups"},
                {"name": "Butter", "quantity": 1, "unit": "cup"},
                {"name": "Brown sugar", "quantity": 0.75, "unit": "cup"},
                {"name": "White sugar", "quantity": 0.75, "unit": "cup"},
                {"name": "Eggs", "quantity": 2, "unit": "whole"},
                {"name": "Vanilla extract", "quantity": 2, "unit": "tsp"},
                {"name": "Chocolate chips", "quantity": 2, "unit": "cups"},
                {"name": "Baking soda", "quantity": 1, "unit": "tsp"},
            ],
            "instructions": [
                "Preheat oven to 375°F (190°C)",
                "Cream together butter and both sugars",
                "Beat in eggs and vanilla",
                "Mix in flour and baking soda",
                "Fold in chocolate chips",
                "Drop spoonfuls onto baking sheet",
                "Bake for 9-11 minutes until golden",
                "Cool on wire rack",
            ],
            "serving_size": 24,
            "prep_time": 15,
            "cook_time": 11,
            "difficulty": "easy",
            "nutritional_info": {
                "calories": 180,
                "protein": 2,
                "carbs": 24,
                "fat": 9,
            },
            "image_url": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e",
            "visibility": "public",
        },
        {
            "title": "Avocado Toast with Poached Egg",
            "description": "Simple and nutritious breakfast with creamy avocado and perfectly poached egg",
            "ingredients": [
                {"name": "Bread", "quantity": 2, "unit": "slices"},
                {"name": "Avocado", "quantity": 1, "unit": "whole"},
                {"name": "Eggs", "quantity": 2, "unit": "whole"},
                {"name": "Lemon juice", "quantity": 1, "unit": "tsp"},
                {"name": "Red pepper flakes", "quantity": 0.5, "unit": "tsp"},
                {"name": "Salt", "quantity": 0.5, "unit": "tsp"},
                {"name": "Black pepper", "quantity": 0.25, "unit": "tsp"},
            ],
            "instructions": [
                "Toast bread until golden brown",
                "Mash avocado with lemon juice, salt, and pepper",
                "Bring water to gentle simmer for poaching eggs",
                "Add a splash of vinegar to water",
                "Crack eggs into water and poach for 3-4 minutes",
                "Spread avocado on toast",
                "Top with poached eggs",
                "Sprinkle with red pepper flakes and serve",
            ],
            "serving_size": 2,
            "prep_time": 5,
            "cook_time": 10,
            "difficulty": "easy",
            "nutritional_info": {
                "calories": 310,
                "protein": 14,
                "carbs": 28,
                "fat": 17,
            },
            "image_url": "https://images.unsplash.com/photo-1541519227354-08fa5d50c44d",
            "visibility": "group",
            "group_id": None,  # Will be set dynamically
        },
        {
            "title": "Beef Tacos",
            "description": "Flavorful ground beef tacos with fresh toppings",
            "ingredients": [
                {"name": "Ground beef", "quantity": 500, "unit": "g"},
                {"name": "Taco seasoning", "quantity": 2, "unit": "tbsp"},
                {"name": "Taco shells", "quantity": 8, "unit": "pieces"},
                {"name": "Lettuce", "quantity": 2, "unit": "cups"},
                {"name": "Tomatoes", "quantity": 2, "unit": "whole"},
                {"name": "Cheese", "quantity": 1, "unit": "cup"},
                {"name": "Sour cream", "quantity": 0.5, "unit": "cup"},
                {"name": "Salsa", "quantity": 0.5, "unit": "cup"},
            ],
            "instructions": [
                "Brown ground beef in a large skillet",
                "Drain excess fat",
                "Add taco seasoning and water, simmer for 5 minutes",
                "Warm taco shells according to package",
                "Chop lettuce and dice tomatoes",
                "Fill shells with seasoned beef",
                "Top with lettuce, tomatoes, cheese, sour cream, and salsa",
                "Serve immediately",
            ],
            "serving_size": 4,
            "prep_time": 10,
            "cook_time": 15,
            "difficulty": "easy",
            "nutritional_info": {
                "calories": 420,
                "protein": 26,
                "carbs": 32,
                "fat": 22,
            },
            "image_url": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47",
            "visibility": "public",
        },
    ]

    # Define tags for each recipe
    recipe_tags_data = [
        # Classic Spaghetti Carbonara
        [
            {"tag_name": "Italian", "tag_category": "cuisine"},
            {"tag_name": "Pasta", "tag_category": "main_ingredient"},
            {"tag_name": "Comfort Food", "tag_category": "meal_type"},
        ],
        # Overnight Oats
        [
            {"tag_name": "Healthy", "tag_category": "dietary"},
            {"tag_name": "No-Cook", "tag_category": "cooking_method"},
            {"tag_name": "Make-Ahead", "tag_category": "meal_type"},
            {"tag_name": "Vegetarian", "tag_category": "dietary"},
        ],
        # Grilled Chicken Caesar Salad
        [
            {"tag_name": "Salad", "tag_category": "meal_type"},
            {"tag_name": "Chicken", "tag_category": "main_ingredient"},
            {"tag_name": "Low-Carb", "tag_category": "dietary"},
            {"tag_name": "Grilled", "tag_category": "cooking_method"},
        ],
        # Homemade Margherita Pizza
        [
            {"tag_name": "Italian", "tag_category": "cuisine"},
            {"tag_name": "Pizza", "tag_category": "meal_type"},
            {"tag_name": "Vegetarian", "tag_category": "dietary"},
            {"tag_name": "Baked", "tag_category": "cooking_method"},
        ],
        # Thai Green Curry
        [
            {"tag_name": "Thai", "tag_category": "cuisine"},
            {"tag_name": "Spicy", "tag_category": "flavor"},
            {"tag_name": "Curry", "tag_category": "meal_type"},
            {"tag_name": "Chicken", "tag_category": "main_ingredient"},
        ],
        # Beef Tacos
        [
            {"tag_name": "Mexican", "tag_category": "cuisine"},
            {"tag_name": "Beef", "tag_category": "main_ingredient"},
            {"tag_name": "Quick", "tag_category": "cooking_method"},
            {"tag_name": "Family-Friendly", "tag_category": "meal_type"},
        ],
    ]

    recipes = []
    for i, recipe_data in enumerate(recipes_data):
        # Distribute recipes among users
        owner = users[i % len(users)]

        # Set group_id for group recipes
        if recipe_data.get("visibility") == "group" and groups:
            recipe_data["group_id"] = groups[0].id

        recipe = Recipe(**recipe_data, owner_id=owner.id)
        db.add(recipe)
        recipes.append(recipe)

    await db.commit()
    for recipe in recipes:
        await db.refresh(recipe)

    # Add tags to recipes
    tags_created = 0
    for i, recipe in enumerate(recipes):
        if i < len(recipe_tags_data):
            for tag_data in recipe_tags_data[i]:
                tag = RecipeTag(
                    recipe_id=recipe.id,
                    tag_name=tag_data["tag_name"],
                    tag_category=tag_data["tag_category"],
                )
                db.add(tag)
                tags_created += 1

    await db.commit()
    print(f"✅ Created {len(recipes)} sample recipes with {tags_created} tags")
    return recipes


async def create_sample_calendars(
    db: AsyncSession, users: list[User], groups: list[Group]
) -> list[Calendar]:
    """Create sample calendars."""
    calendars = []
    for i, user in enumerate(users):
        # Make some calendars group-shared
        if i == 1 and groups:  # demo user's calendar is group-shared
            calendar = Calendar(
                name=f"{user.username}'s Meal Plan",
                owner_id=user.id,
                visibility="group",
                group_id=groups[0].id,
            )
        else:
            calendar = Calendar(
                name=f"{user.username}'s Meal Plan",
                owner_id=user.id,
                visibility="private",
            )
        db.add(calendar)
        calendars.append(calendar)

    await db.commit()
    for calendar in calendars:
        await db.refresh(calendar)

    print(f"✅ Created {len(calendars)} sample calendars")
    return calendars


async def create_sample_calendar_meals(
    db: AsyncSession, calendars: list[Calendar], recipes: list[Recipe]
) -> None:
    """Create sample calendar meals for the next week."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    meal_types = ["breakfast", "lunch", "dinner"]

    meals_created = 0
    for calendar in calendars:
        # Add meals for the next 7 days
        for day_offset in range(7):
            meal_date = today + timedelta(days=day_offset)

            # Add 2-3 meals per day
            for meal_type in meal_types[: 2 + (day_offset % 2)]:
                # Pick a recipe based on index
                recipe_index = (day_offset + len(meal_type)) % len(recipes)
                recipe = recipes[recipe_index]

                meal = CalendarMeal(
                    calendar_id=calendar.id,
                    recipe_id=recipe.id,
                    meal_date=meal_date,
                    meal_type=meal_type,
                )
                db.add(meal)
                meals_created += 1

    await db.commit()
    print(f"✅ Created {meals_created} sample calendar meals")


async def populate_database():
    """Main function to populate database with all sample data."""
    print("🍽️  Populating database with sample data...")
    print("=" * 50)

    async with AsyncSessionLocal() as db:  # type: ignore
        try:
            # Create sample data
            users = await create_sample_users(db)
            groups = await create_sample_groups(db, users)
            recipes = await create_sample_recipes(db, users, groups)
            calendars = await create_sample_calendars(db, users, groups)
            await create_sample_calendar_meals(db, calendars, recipes)

            print("=" * 50)
            print("✨ Database population complete!")
            print()
            print("Sample Users:")
            print("  - admin (admin@example.com) - Password: 'admin123' [ADMIN]")
            print("  - demo (demo@example.com) - Password: 'password123'")
            print("  - chef_alice (alice@example.com) - Password: 'password123'")
            print("  - foodie_bob (bob@example.com) - Password: 'password123'")
            print()
            print("Sample Group:")
            print("  - Family Recipes (owner: demo, members: chef_alice [admin], foodie_bob)")
            print()
            print("You can now login and explore the application!")

        except Exception as e:
            print(f"❌ Error populating database: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(populate_database())
