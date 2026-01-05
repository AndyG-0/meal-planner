"""Nutrition calculation service."""

from typing import Any

# Basic nutrition database (simplified - in production this would be a proper database or API)
NUTRITION_DB = {
    # Proteins (per 100g)
    "chicken breast": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0},
    "beef": {"calories": 250, "protein": 26, "carbs": 0, "fat": 17, "fiber": 0},
    "salmon": {"calories": 208, "protein": 20, "carbs": 0, "fat": 13, "fiber": 0},
    "eggs": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11, "fiber": 0},
    "tofu": {"calories": 76, "protein": 8, "carbs": 1.9, "fat": 4.8, "fiber": 0.3},
    # Carbs (per 100g)
    "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4},
    "pasta": {"calories": 131, "protein": 5, "carbs": 25, "fat": 1.1, "fiber": 1.8},
    "bread": {"calories": 265, "protein": 9, "carbs": 49, "fat": 3.2, "fiber": 2.7},
    "potato": {"calories": 77, "protein": 2, "carbs": 17, "fat": 0.1, "fiber": 2.1},
    "oats": {"calories": 389, "protein": 17, "carbs": 66, "fat": 6.9, "fiber": 10.6},
    # Vegetables (per 100g)
    "broccoli": {"calories": 34, "protein": 2.8, "carbs": 7, "fat": 0.4, "fiber": 2.6},
    "spinach": {"calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "fiber": 2.2},
    "tomato": {"calories": 18, "protein": 0.9, "carbs": 3.9, "fat": 0.2, "fiber": 1.2},
    "carrot": {"calories": 41, "protein": 0.9, "carbs": 10, "fat": 0.2, "fiber": 2.8},
    "onion": {"calories": 40, "protein": 1.1, "carbs": 9, "fat": 0.1, "fiber": 1.7},
    # Fruits (per 100g)
    "apple": {"calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2, "fiber": 2.4},
    "banana": {"calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3, "fiber": 2.6},
    "orange": {"calories": 47, "protein": 0.9, "carbs": 12, "fat": 0.1, "fiber": 2.4},
    # Dairy (per 100ml/100g)
    "milk": {"calories": 42, "protein": 3.4, "carbs": 5, "fat": 1, "fiber": 0},
    "cheese": {"calories": 402, "protein": 25, "carbs": 1.3, "fat": 33, "fiber": 0},
    "yogurt": {"calories": 59, "protein": 10, "carbs": 3.6, "fat": 0.4, "fiber": 0},
    # Fats (per 100g)
    "olive oil": {"calories": 884, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0},
    "butter": {"calories": 717, "protein": 0.9, "carbs": 0.1, "fat": 81, "fiber": 0},
    # Nuts (per 100g)
    "almonds": {"calories": 579, "protein": 21, "carbs": 22, "fat": 50, "fiber": 12.5},
    "peanuts": {"calories": 567, "protein": 26, "carbs": 16, "fat": 49, "fiber": 8.5},
}

# Unit conversions to grams
UNIT_CONVERSIONS = {
    "g": 1,
    "gram": 1,
    "grams": 1,
    "kg": 1000,
    "kilogram": 1000,
    "kilograms": 1000,
    "oz": 28.35,
    "ounce": 28.35,
    "ounces": 28.35,
    "lb": 453.592,
    "pound": 453.592,
    "pounds": 453.592,
    "cup": 240,  # Approximate, varies by ingredient
    "cups": 240,
    "tbsp": 15,
    "tablespoon": 15,
    "tablespoons": 15,
    "tsp": 5,
    "teaspoon": 5,
    "teaspoons": 5,
    "ml": 1,  # For liquids, assume 1ml = 1g
    "milliliter": 1,
    "milliliters": 1,
    "l": 1000,
    "liter": 1000,
    "liters": 1000,
}


def normalize_ingredient_name(name: str) -> str:
    """Normalize ingredient name for lookup."""
    name = name.lower().strip()
    # Remove common words
    for word in ["raw", "cooked", "fresh", "frozen", "organic", "sliced", "diced", "chopped"]:
        name = name.replace(word, "").strip()
    return name


def convert_to_grams(quantity: float, unit: str) -> float:
    """Convert quantity to grams."""
    unit_lower = unit.lower().strip()
    conversion_factor = UNIT_CONVERSIONS.get(unit_lower, 1)
    return quantity * conversion_factor


def calculate_nutrition_for_ingredient(ingredient: dict[str, Any]) -> dict[str, float]:
    """Calculate nutrition for a single ingredient."""
    name = normalize_ingredient_name(ingredient.get("name", ""))
    quantity_val = ingredient.get("quantity", 0)
    # Treat explicit None as 0 to avoid TypeError when converting
    if quantity_val is None:
        quantity = 0.0
    else:
        quantity = float(quantity_val)
    unit = ingredient.get("unit", "g")

    # Convert to grams
    grams = convert_to_grams(quantity, unit)

    # Find nutrition data
    nutrition_data = None
    for key in NUTRITION_DB:
        if key in name or name in key:
            nutrition_data = NUTRITION_DB[key]
            break

    if not nutrition_data:
        # Return zeros if not found
        return {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0,
        }

    # Calculate based on 100g reference
    multiplier = grams / 100

    return {
        "calories": round(nutrition_data["calories"] * multiplier, 1),
        "protein": round(nutrition_data["protein"] * multiplier, 1),
        "carbs": round(nutrition_data["carbs"] * multiplier, 1),
        "fat": round(nutrition_data["fat"] * multiplier, 1),
        "fiber": round(nutrition_data["fiber"] * multiplier, 1),
    }


def calculate_recipe_nutrition(
    ingredients: list[dict[str, Any]],
    serving_size: int = 4,
) -> dict[str, Any]:
    """Calculate total nutrition for a recipe."""
    total = {
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fat": 0,
        "fiber": 0,
    }

    for ingredient in ingredients:
        nutrition = calculate_nutrition_for_ingredient(ingredient)
        for key in total:
            total[key] += nutrition[key]

    # Calculate per serving
    per_serving = {f"{key}_per_serving": round(total[key] / serving_size, 1) for key in total}

    return {
        "total": total,
        "per_serving": per_serving,
        "serving_size": serving_size,
    }
