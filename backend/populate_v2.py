"""Populate database with 500 diverse recipes for testing pagination and scaling."""

import asyncio
import random
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Group, Recipe, RecipeTag, User
from app.utils.auth import get_password_hash

# Recipe templates for different categories
RECIPE_TEMPLATES = {
    "breakfast": [
        "Pancakes",
        "French Toast",
        "Omelet",
        "Smoothie Bowl",
        "Breakfast Burrito",
        "Waffles",
        "Eggs Benedict",
        "Breakfast Sandwich",
        "Granola",
        "Muffins",
        "Bagels",
        "Crepes",
        "Hash Browns",
        "Breakfast Casserole",
        "Porridge",
        "Scones",
        "Danish Pastry",
        "Croissant",
        "Quiche",
        "Frittata",
    ],
    "lunch": [
        "Sandwich",
        "Salad",
        "Wrap",
        "Soup",
        "Burger",
        "Pasta Salad",
        "Rice Bowl",
        "Tacos",
        "Quesadilla",
        "Pizza",
        "Stir Fry",
        "Fried Rice",
        "Noodle Bowl",
        "Bento Box",
        "Sushi Roll",
        "Poke Bowl",
        "Burrito Bowl",
        "Grain Bowl",
        "Buddha Bowl",
        "Chili",
    ],
    "dinner": [
        "Roast Chicken",
        "Steak",
        "Salmon",
        "Pasta",
        "Curry",
        "Lasagna",
        "Casserole",
        "Stew",
        "Risotto",
        "Paella",
        "Pot Roast",
        "Meatloaf",
        "Stuffed Peppers",
        "Enchiladas",
        "Fajitas",
        "Shepherd's Pie",
        "Fish and Chips",
        "Goulash",
        "Ratatouille",
        "Biryani",
    ],
    "snack": [
        "Energy Balls",
        "Trail Mix",
        "Popcorn",
        "Chips",
        "Crackers",
        "Fruit Salad",
        "Veggie Sticks",
        "Hummus",
        "Guacamole",
        "Salsa",
        "Bruschetta",
        "Crostini",
        "Spring Rolls",
        "Samosas",
        "Empanadas",
        "Deviled Eggs",
        "Stuffed Mushrooms",
        "Cheese Board",
        "Nuts",
        "Pretzels",
    ],
    "dessert": [
        "Chocolate Cake",
        "Brownies",
        "Cookies",
        "Ice Cream",
        "Cheesecake",
        "Pie",
        "Tart",
        "Cupcakes",
        "Pudding",
        "Mousse",
        "Tiramisu",
        "Creme Brulee",
        "Panna Cotta",
        "Flan",
        "Trifle",
        "Macarons",
        "Eclairs",
        "Profiteroles",
        "Baklava",
        "Cannoli",
    ],
    "staple": [
        "Tomato Sauce",
        "Pesto",
        "Stock",
        "Dough",
        "Marinade",
        "Dressing",
        "Gravy",
        "Bechamel",
        "Hollandaise",
        "Aioli",
        "Chimichurri",
        "Tzatziki",
        "Salsa Verde",
        "BBQ Sauce",
        "Hot Sauce",
        "Pickles",
        "Jam",
        "Chutney",
        "Compote",
        "Syrup",
    ],
    "frozen": [
        "Frozen Pizza",
        "TV Dinner",
        "Frozen Burritos",
        "Ice Cream Sandwiches",
        "Frozen Pot Pie",
        "Frozen Lasagna",
        "Frozen Soup",
        "Frozen Stir Fry",
        "Frozen Dumplings",
        "Frozen Spring Rolls",
    ],
}

# Cuisine types
CUISINES = [
    "Italian",
    "Mexican",
    "Chinese",
    "Japanese",
    "Thai",
    "Indian",
    "French",
    "Greek",
    "Spanish",
    "Korean",
    "Vietnamese",
    "American",
    "Mediterranean",
    "Middle Eastern",
    "Caribbean",
    "British",
    "German",
    "Turkish",
    "Brazilian",
    "Moroccan",
]

# Main ingredients
MAIN_INGREDIENTS = [
    "Chicken",
    "Beef",
    "Pork",
    "Fish",
    "Shrimp",
    "Tofu",
    "Eggs",
    "Cheese",
    "Pasta",
    "Rice",
    "Quinoa",
    "Beans",
    "Lentils",
    "Vegetables",
    "Mushrooms",
    "Salmon",
    "Tuna",
    "Lamb",
    "Turkey",
    "Duck",
]

# Dietary tags
DIETARY_TAGS = [
    "Vegetarian",
    "Vegan",
    "Gluten-Free",
    "Dairy-Free",
    "Keto",
    "Paleo",
    "Low-Carb",
    "High-Protein",
    "Nut-Free",
    "Egg-Free",
]

# Cooking methods
COOKING_METHODS = [
    "Baked",
    "Grilled",
    "Fried",
    "Steamed",
    "Roasted",
    "Sauteed",
    "Slow-Cooked",
    "Pressure-Cooked",
    "Air-Fried",
    "No-Cook",
    "One-Pot",
]

# Flavor profiles
FLAVORS = [
    "Spicy",
    "Sweet",
    "Savory",
    "Tangy",
    "Smoky",
    "Herby",
    "Garlicky",
    "Citrusy",
    "Creamy",
    "Crunchy",
]

# Meal type tags
MEAL_TYPE_TAGS = [
    "Quick",
    "Make-Ahead",
    "Comfort Food",
    "Healthy",
    "Family-Friendly",
    "Budget-Friendly",
    "Gourmet",
    "Holiday",
    "Party Food",
    "Meal Prep",
]


def generate_recipe_name(category: str, cuisine: str, main_ingredient: str, template: str) -> str:
    """Generate a recipe name combining various elements."""
    modifiers = [
        "Classic",
        "Authentic",
        "Modern",
        "Traditional",
        "Homemade",
        "Easy",
        "Best",
        "Perfect",
        "Ultimate",
        "Quick",
    ]

    patterns = [
        f"{template}",
        f"{cuisine} {template}",
        f"{main_ingredient} {template}",
        f"{cuisine} {main_ingredient} {template}",
        f"{random.choice(modifiers)} {template}",
        f"{random.choice(modifiers)} {cuisine} {template}",
    ]

    return random.choice(patterns)


def generate_ingredients(main_ingredient: str, category: str) -> list[dict]:
    """Generate a list of ingredients for a recipe."""
    base_ingredients = [
        {
            "name": main_ingredient,
            "quantity": random.randint(1, 4),
            "unit": random.choice(["cups", "lbs", "pieces", "oz"]),
        },
    ]

    common_ingredients = [
        {"name": "Salt", "quantity": 1, "unit": "tsp"},
        {"name": "Pepper", "quantity": 0.5, "unit": "tsp"},
        {"name": "Olive oil", "quantity": 2, "unit": "tbsp"},
        {"name": "Garlic", "quantity": 2, "unit": "cloves"},
        {"name": "Onion", "quantity": 1, "unit": "whole"},
    ]

    category_ingredients = {
        "breakfast": ["Eggs", "Milk", "Butter", "Sugar", "Flour"],
        "lunch": ["Lettuce", "Tomato", "Cucumber", "Cheese", "Bread"],
        "dinner": ["Rice", "Potatoes", "Vegetables", "Broth", "Herbs"],
        "snack": ["Nuts", "Seeds", "Honey", "Fruits", "Yogurt"],
        "dessert": ["Sugar", "Flour", "Butter", "Vanilla", "Chocolate"],
        "staple": ["Herbs", "Spices", "Vinegar", "Oil", "Lemon"],
        "frozen": ["Sauce", "Cheese", "Vegetables", "Spices", "Broth"],
    }

    extras = category_ingredients.get(category, ["Seasoning", "Water"])
    num_extras = random.randint(3, 7)

    for i in range(num_extras):
        extra = random.choice(extras)
        base_ingredients.append(
            {
                "name": extra,
                "quantity": round(random.uniform(0.25, 3), 2),
                "unit": random.choice(["cup", "cups", "tbsp", "tsp", "oz", "g"]),
            }
        )

    # Add some common seasonings
    base_ingredients.extend(random.sample(common_ingredients, k=random.randint(2, 4)))

    return base_ingredients


def generate_instructions(num_steps: int) -> list[str]:
    """Generate cooking instructions."""
    instruction_templates = [
        "Preheat oven to {temp}°F ({temp_c}°C)",
        "In a large bowl, mix together {ingredients}",
        "Heat {oil} in a pan over medium heat",
        "Add {ingredient} and cook for {time} minutes",
        "Season with salt and pepper to taste",
        "Stir occasionally until {result}",
        "Transfer to a baking dish",
        "Bake for {time} minutes until {result}",
        "Let rest for {time} minutes before serving",
        "Garnish with fresh herbs and serve",
        "Combine all ingredients in a pot",
        "Bring to a boil, then reduce heat",
        "Simmer for {time} minutes",
        "Drain and set aside",
        "Mix together wet and dry ingredients separately",
        "Fold wet ingredients into dry ingredients",
        "Pour into prepared pan",
        "Chill in refrigerator for {time} minutes",
        "Serve hot/cold and enjoy",
    ]

    instructions = []
    for i in range(min(num_steps, len(instruction_templates))):
        template = random.choice(instruction_templates)
        template = template.replace("{temp}", str(random.choice([325, 350, 375, 400, 425])))
        template = template.replace("{temp_c}", str(random.choice([160, 175, 190, 200, 220])))
        template = template.replace("{ingredients}", "the ingredients")
        template = template.replace("{ingredient}", "ingredients")
        template = template.replace("{oil}", "olive oil")
        template = template.replace("{time}", str(random.randint(5, 30)))
        template = template.replace(
            "{result}", random.choice(["golden brown", "tender", "cooked through", "fragrant"])
        )
        instructions.append(template)

    return instructions[:num_steps]


def generate_nutritional_info(category: str) -> dict:
    """Generate realistic nutritional information based on category."""
    base_calories = {
        "breakfast": (250, 500),
        "lunch": (350, 650),
        "dinner": (400, 800),
        "snack": (100, 300),
        "dessert": (200, 600),
        "staple": (50, 200),
        "frozen": (300, 700),
    }

    cal_range = base_calories.get(category, (200, 600))
    calories = random.randint(*cal_range)

    # Calculate macros based on calories
    protein = random.randint(5, int(calories * 0.3 / 4))
    carbs = random.randint(10, int(calories * 0.5 / 4))
    fat = random.randint(5, int(calories * 0.35 / 9))

    return {"calories": calories, "protein": protein, "carbs": carbs, "fat": fat}


def get_recipe_tags(category: str, cuisine: str, main_ingredient: str) -> list[dict]:
    """Generate tags for a recipe."""
    tags = []

    # Add cuisine tag
    if cuisine:
        tags.append({"tag_name": cuisine, "tag_category": "cuisine"})

    # Add main ingredient tag
    if main_ingredient:
        tags.append({"tag_name": main_ingredient, "tag_category": "main_ingredient"})

    # Add dietary tags (random selection)
    if random.random() < 0.4:  # 40% chance
        dietary_tag = random.choice(DIETARY_TAGS)
        tags.append({"tag_name": dietary_tag, "tag_category": "dietary"})

    # Add cooking method tag
    if random.random() < 0.6:  # 60% chance
        method = random.choice(COOKING_METHODS)
        tags.append({"tag_name": method, "tag_category": "cooking_method"})

    # Add flavor tag
    if random.random() < 0.5:  # 50% chance
        flavor = random.choice(FLAVORS)
        tags.append({"tag_name": flavor, "tag_category": "flavor"})

    # Add meal type tags
    if random.random() < 0.7:  # 70% chance
        meal_type = random.choice(MEAL_TYPE_TAGS)
        tags.append({"tag_name": meal_type, "tag_category": "meal_type"})

    return tags


async def create_test_users(db: AsyncSession) -> list[User]:
    """Create test users if they don't exist."""
    # Check if ANY users already exist
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.deleted_at.is_(None)).limit(1))
    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        print("✅ Using existing users")
        result = await db.execute(select(User).where(User.deleted_at.is_(None)))
        all_users = list(result.scalars().all())
        print(f"✅ Found {len(all_users)} existing users")
        return all_users

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

    print(f"✅ Created {len(users)} test users")
    return users


async def create_test_groups(db: AsyncSession, users: list[User]) -> list[Group]:
    """Create test groups if they don't exist."""
    from sqlalchemy import select

    result = await db.execute(select(Group).where(Group.name == "Family Recipes"))
    existing_group = result.scalar_one_or_none()

    if existing_group:
        print("✅ Using existing groups")
        result = await db.execute(select(Group))
        return list(result.scalars().all())

    family_group = Group(
        name="Family Recipes",
        owner_id=users[1].id if len(users) > 1 else users[0].id,
    )
    db.add(family_group)
    await db.commit()
    await db.refresh(family_group)

    print("✅ Created test group")
    return [family_group]


async def generate_500_recipes(
    db: AsyncSession, users: list[User], groups: list[Group]
) -> list[Recipe]:
    """Generate 500 diverse recipes."""
    recipes = []
    recipe_count = 0
    target_count = 500

    print(f"🍳 Generating {target_count} diverse recipes...")

    categories = list(RECIPE_TEMPLATES.keys())

    for category in categories:
        templates = RECIPE_TEMPLATES[category]
        # Calculate how many recipes per category
        recipes_per_category = target_count // len(categories)

        for i in range(recipes_per_category):
            template = random.choice(templates)
            cuisine = random.choice(CUISINES)
            main_ingredient = random.choice(MAIN_INGREDIENTS)

            title = generate_recipe_name(category, cuisine, main_ingredient, template)

            # Ensure unique titles
            counter = 1
            original_title = title
            while any(r.title == title for r in recipes):
                title = f"{original_title} {counter}"
                counter += 1

            # Random description
            descriptions = [
                f"Delicious {cuisine.lower()} {template.lower()} made with {main_ingredient.lower()}",
                f"A {random.choice(['classic', 'modern', 'traditional', 'unique'])} take on {template.lower()}",
                f"Perfect {template.lower()} for any occasion",
                f"{random.choice(['Easy', 'Quick', 'Simple', 'Amazing'])} {template.lower()} recipe",
                f"Authentic {cuisine.lower()} {template.lower()} with amazing flavor",
            ]

            description = random.choice(descriptions)

            # Generate recipe data
            ingredients = generate_ingredients(main_ingredient, category)
            instructions = generate_instructions(random.randint(5, 12))
            nutritional_info = generate_nutritional_info(category)

            # Random times and difficulty
            prep_time = random.randint(5, 60)
            cook_time = random.randint(0, 120) if category != "snack" else random.randint(0, 30)
            difficulty = random.choice(["easy", "medium", "hard"])
            serving_size = random.choice([1, 2, 4, 6, 8])

            # Random visibility
            visibility_options = ["private", "group", "public"]
            weights = [0.3, 0.3, 0.4]  # 30% private, 30% group, 40% public
            visibility = random.choices(visibility_options, weights=weights)[0]

            # Assign owner
            owner = random.choice(users)

            # Set group_id for group recipes
            group_id = None
            if visibility == "group" and groups:
                group_id = random.choice(groups).id

            # Random image (using unsplash food images)
            image_ids = [
                "photo-1546069901-ba9599a7e63c",
                "photo-1504674900247-0877df9cc836",
                "photo-1567620905732-2d1ec7ab7445",
                "photo-1565299624946-b28f40a0ae38",
                "photo-1540189549336-e6e99c3679fe",
                "photo-1565958011703-44f9829ba187",
                "photo-1482049016688-2d3e1b311543",
                "photo-1476224203421-9ac39bcb3327",
            ]
            image_url = f"https://images.unsplash.com/{random.choice(image_ids)}"

            recipe = Recipe(
                title=title,
                description=description,
                owner_id=owner.id,
                ingredients=ingredients,
                instructions=instructions,
                image_url=image_url,
                serving_size=serving_size,
                prep_time=prep_time,
                cook_time=cook_time,
                difficulty=difficulty,
                category=category,
                nutritional_info=nutritional_info,
                visibility=visibility,
                group_id=group_id,
            )

            db.add(recipe)
            recipes.append(recipe)
            recipe_count += 1

            # Commit in batches
            if recipe_count % 50 == 0:
                await db.commit()
                for r in recipes[-50:]:
                    await db.refresh(r)
                print(f"  ✓ Created {recipe_count}/{target_count} recipes...")

    # Final commit for remaining recipes
    await db.commit()
    for recipe in recipes:
        await db.refresh(recipe)

    print(f"✅ Created {len(recipes)} diverse recipes")
    return recipes


async def add_tags_to_recipes(db: AsyncSession, recipes: list[Recipe]) -> None:
    """Add tags to all recipes."""
    print("🏷️  Adding tags to recipes...")

    tags_created = 0
    for i, recipe in enumerate(recipes):
        # Get tags based on recipe properties
        tags_data = get_recipe_tags(
            recipe.category,
            random.choice(CUISINES),  # Use cuisine from title if possible
            random.choice(MAIN_INGREDIENTS),
        )

        for tag_data in tags_data:
            tag = RecipeTag(
                recipe_id=recipe.id,
                tag_name=tag_data["tag_name"],
                tag_category=tag_data["tag_category"],
            )
            db.add(tag)
            tags_created += 1

        # Commit in batches
        if (i + 1) % 50 == 0:
            await db.commit()
            print(f"  ✓ Added tags to {i + 1}/{len(recipes)} recipes...")

    await db.commit()
    print(f"✅ Created {tags_created} tags for {len(recipes)} recipes")


async def populate_500_recipes():
    """Main function to populate database with 500 recipes."""
    print("🍽️  Populating database with 500 recipes for testing...")
    print("=" * 60)

    async with AsyncSessionLocal() as db:  # type: ignore
        try:
            # Create or get users and groups
            users = await create_test_users(db)
            groups = await create_test_groups(db, users)

            # Generate 500 recipes
            recipes = await generate_500_recipes(db, users, groups)

            # Add tags to all recipes
            await add_tags_to_recipes(db, recipes)

            print("=" * 60)
            print("✨ Database population complete!")
            print()
            print("📊 Summary:")
            print(f"  - {len(recipes)} recipes created")
            print(f"  - {len(users)} users")
            print(f"  - {len(groups)} groups")
            print()

            # Print category breakdown
            category_counts = {}
            for recipe in recipes:
                category_counts[recipe.category] = category_counts.get(recipe.category, 0) + 1

            print("📁 Recipes by category:")
            for category, count in sorted(category_counts.items()):
                print(f"  - {category}: {count}")
            print()

            # Print visibility breakdown
            visibility_counts = {}
            for recipe in recipes:
                visibility_counts[recipe.visibility] = (
                    visibility_counts.get(recipe.visibility, 0) + 1
                )

            print("👁️  Recipes by visibility:")
            for visibility, count in sorted(visibility_counts.items()):
                print(f"  - {visibility}: {count}")

        except Exception as e:
            print(f"❌ Error populating database: {e}")
            import traceback

            traceback.print_exc()
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(populate_500_recipes())
