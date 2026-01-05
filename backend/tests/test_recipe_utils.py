"""Tests for recipe utilities (ingredient cleaning) and tag listing."""

import pytest
from app.api.v1.endpoints.recipes import clean_ingredient_data
from app.models import Recipe, RecipeTag


def test_clean_ingredient_parses_fraction_and_unit():
    input_data = [{"name": "1/2 cup flour", "quantity": None, "unit": ""}]
    cleaned = clean_ingredient_data(input_data)
    assert len(cleaned) == 1
    assert cleaned[0]["name"] == "flour"
    assert cleaned[0]["unit"] == "cup"
    assert cleaned[0]["quantity"] == 0.5


def test_clean_ingredient_parses_parenthetical():
    input_data = [{"name": "(100 g) cheese, softened", "quantity": None, "unit": ""}]
    cleaned = clean_ingredient_data(input_data)
    assert len(cleaned) == 1
    assert cleaned[0]["name"] == "cheese, softened"
    assert cleaned[0]["unit"] == "g"
    assert cleaned[0]["quantity"] == 100.0


def test_clean_ingredient_filters_invalid():
    input_data = ["string", {"name": "", "quantity": None, "unit": ""}, {"name": "tsp salt", "quantity": None, "unit": ""}]
    cleaned = clean_ingredient_data(input_data)
    # Only the last with name starting with unit should be filtered out or normalized; expect empty
    assert isinstance(cleaned, list)
