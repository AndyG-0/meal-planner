"""Grocery list endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, GroceryList, Calendar, CalendarMeal, Recipe
from app.schemas import GroceryListCreate, GroceryListResponse, GroceryListItem
from app.api.v1.dependencies import get_current_active_user

router = APIRouter(prefix="/grocery-lists", tags=["Grocery Lists"])


def consolidate_ingredients(recipes: list[Recipe]) -> list[dict]:
    """Consolidate ingredients from multiple recipes."""
    ingredient_map = {}
    
    for recipe in recipes:
        for ingredient in recipe.ingredients:
            name = ingredient["name"].lower()
            quantity = float(ingredient["quantity"])
            unit = ingredient["unit"]
            
            if name in ingredient_map:
                # Simple consolidation - same unit
                if ingredient_map[name]["unit"] == unit:
                    ingredient_map[name]["quantity"] += quantity
                else:
                    # Different units - keep separate for now
                    # TODO: Implement unit conversion
                    key = f"{name}_{unit}"
                    if key in ingredient_map:
                        ingredient_map[key]["quantity"] += quantity
                    else:
                        ingredient_map[key] = {
                            "name": name,
                            "quantity": quantity,
                            "unit": unit,
                            "category": None,
                            "checked": False,
                        }
            else:
                ingredient_map[name] = {
                    "name": name,
                    "quantity": quantity,
                    "unit": unit,
                    "category": None,
                    "checked": False,
                }
    
    return list(ingredient_map.values())


@router.post("", response_model=GroceryListResponse, status_code=status.HTTP_201_CREATED)
async def create_grocery_list(
    list_data: GroceryListCreate,
    calendar_id: int = Query(..., description="Calendar ID to generate list from"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GroceryList:
    """Create a grocery list from calendar meals."""
    # Check if calendar exists and user has permission
    result = await db.execute(
        select(Calendar).where(Calendar.id == calendar_id)
    )
    calendar = result.scalar_one_or_none()
    
    if not calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found",
        )
    
    if calendar.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this calendar",
        )
    
    # Get meals in date range
    query = select(CalendarMeal).where(CalendarMeal.calendar_id == calendar_id)
    
    if list_data.date_from:
        query = query.where(CalendarMeal.meal_date >= list_data.date_from)
    if list_data.date_to:
        query = query.where(CalendarMeal.meal_date <= list_data.date_to)
    
    result = await db.execute(query)
    meals = result.scalars().all()
    
    # Get recipes
    recipe_ids = [meal.recipe_id for meal in meals]
    result = await db.execute(
        select(Recipe).where(
            Recipe.id.in_(recipe_ids),
            Recipe.deleted_at.is_(None),
        )
    )
    recipes = result.scalars().all()
    
    # Consolidate ingredients
    items = consolidate_ingredients(list(recipes))
    
    # Create grocery list
    grocery_list = GroceryList(
        user_id=current_user.id,
        name=list_data.name,
        date_from=list_data.date_from,
        date_to=list_data.date_to,
        items=items,
    )
    db.add(grocery_list)
    await db.commit()
    await db.refresh(grocery_list)
    
    return grocery_list


@router.get("", response_model=list[GroceryListResponse])
async def list_grocery_lists(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[GroceryList]:
    """List user's grocery lists."""
    result = await db.execute(
        select(GroceryList).where(GroceryList.user_id == current_user.id)
    )
    lists = result.scalars().all()
    return list(lists)


@router.get("/{list_id}", response_model=GroceryListResponse)
async def get_grocery_list(
    list_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GroceryList:
    """Get a grocery list by ID."""
    result = await db.execute(
        select(GroceryList).where(GroceryList.id == list_id)
    )
    grocery_list = result.scalar_one_or_none()
    
    if not grocery_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grocery list not found",
        )
    
    if grocery_list.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this grocery list",
        )
    
    return grocery_list


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grocery_list(
    list_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a grocery list."""
    result = await db.execute(
        select(GroceryList).where(GroceryList.id == list_id)
    )
    grocery_list = result.scalar_one_or_none()
    
    if not grocery_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grocery list not found",
        )
    
    if grocery_list.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this grocery list",
        )
    
    await db.delete(grocery_list)
    await db.commit()
