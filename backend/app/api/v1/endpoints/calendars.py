"""Calendar endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user
from app.database import get_db
from app.models import Calendar, CalendarMeal, Recipe, User
from app.schemas import (
    CalendarCreate,
    CalendarMealCreate,
    CalendarMealResponse,
    CalendarResponse,
    CalendarUpdate,
)

router = APIRouter(prefix="/calendars", tags=["Calendars"])


@router.post("", response_model=CalendarResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar(
    calendar_data: CalendarCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Calendar:
    """Create a new calendar."""
    calendar = Calendar(
        **calendar_data.model_dump(),
        owner_id=current_user.id,
    )
    db.add(calendar)
    await db.commit()
    await db.refresh(calendar)
    return calendar


@router.get("", response_model=list[CalendarResponse])
async def list_calendars(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[Calendar]:
    """List user's calendars."""
    result = await db.execute(
        select(Calendar).where(Calendar.owner_id == current_user.id)
    )
    calendars = result.scalars().all()
    return list(calendars)


@router.get("/{calendar_id}", response_model=CalendarResponse)
async def get_calendar(
    calendar_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Calendar:
    """Get a calendar by ID."""
    result = await db.execute(select(Calendar).where(Calendar.id == calendar_id))
    calendar = result.scalar_one_or_none()

    if not calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found",
        )

    # Check access permissions
    if calendar.owner_id != current_user.id:
        # TODO: Check group membership for shared calendars
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this calendar",
        )

    return calendar


@router.put("/{calendar_id}", response_model=CalendarResponse)
async def update_calendar(
    calendar_id: int,
    calendar_data: CalendarUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Calendar:
    """Update a calendar."""
    result = await db.execute(select(Calendar).where(Calendar.id == calendar_id))
    calendar = result.scalar_one_or_none()

    if not calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found",
        )

    if calendar.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this calendar",
        )

    # Update calendar fields
    update_data = calendar_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(calendar, field, value)

    await db.commit()
    await db.refresh(calendar)
    return calendar


@router.delete("/{calendar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar(
    calendar_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a calendar."""
    result = await db.execute(select(Calendar).where(Calendar.id == calendar_id))
    calendar = result.scalar_one_or_none()

    if not calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found",
        )

    if calendar.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this calendar",
        )

    await db.delete(calendar)
    await db.commit()


@router.post(
    "/{calendar_id}/meals",
    response_model=CalendarMealResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_meal_to_calendar(
    calendar_id: int,
    meal_data: CalendarMealCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarMeal:
    """Add a meal to a calendar."""
    # Check if calendar exists and user has permission
    result = await db.execute(select(Calendar).where(Calendar.id == calendar_id))
    calendar = result.scalar_one_or_none()

    if not calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found",
        )

    if calendar.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this calendar",
        )

    # Check if recipe exists
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == meal_data.recipe_id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    # Create meal
    meal = CalendarMeal(
        calendar_id=calendar_id,
        **meal_data.model_dump(),
    )
    db.add(meal)
    await db.commit()
    await db.refresh(meal)
    return meal


@router.get("/{calendar_id}/meals", response_model=list[CalendarMealResponse])
async def list_calendar_meals(
    calendar_id: int,
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[CalendarMeal]:
    """List meals in a calendar."""
    # Check if calendar exists and user has permission
    result = await db.execute(select(Calendar).where(Calendar.id == calendar_id))
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

    # Build query
    query = select(CalendarMeal).where(CalendarMeal.calendar_id == calendar_id)

    if date_from:
        query = query.where(CalendarMeal.meal_date >= date_from)
    if date_to:
        query = query.where(CalendarMeal.meal_date <= date_to)

    result = await db.execute(query)
    meals = result.scalars().all()
    return list(meals)


@router.delete("/{calendar_id}/meals/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_meal_from_calendar(
    calendar_id: int,
    meal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a meal from a calendar."""
    # Check if calendar exists and user has permission
    result = await db.execute(select(Calendar).where(Calendar.id == calendar_id))
    calendar = result.scalar_one_or_none()

    if not calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found",
        )

    if calendar.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this calendar",
        )

    # Get meal
    result = await db.execute(
        select(CalendarMeal).where(
            CalendarMeal.id == meal_id,
            CalendarMeal.calendar_id == calendar_id,
        )
    )
    meal = result.scalar_one_or_none()

    if not meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal not found",
        )

    await db.delete(meal)
    await db.commit()
