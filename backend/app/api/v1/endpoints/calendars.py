"""Calendar endpoints."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user
from app.database import get_db
from app.models import Calendar, CalendarMeal, Recipe, User
from app.schemas import (
    CalendarCopyRequest,
    CalendarCopyResponse,
    CalendarCreate,
    CalendarMealCreate,
    CalendarMealResponse,
    CalendarPrepopulateRequest,
    CalendarPrepopulateResponse,
    CalendarResponse,
    CalendarUpdate,
)
from app.services.calendar_prepopulate import CalendarPrepopulateService

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
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[Calendar]:
    """List user's calendars with pagination."""
    result = await db.execute(
        select(Calendar).where(Calendar.owner_id == current_user.id).offset(skip).limit(limit)
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
    # Convert timezone-aware datetime to naive (UTC) for storage
    meal_dict = meal_data.model_dump()
    if meal_dict["meal_date"].tzinfo:
        meal_dict["meal_date"] = meal_dict["meal_date"].replace(tzinfo=None)

    meal = CalendarMeal(
        calendar_id=calendar_id,
        **meal_dict,
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
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[CalendarMeal]:
    """List meals in a calendar with pagination."""
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

    # Build query with recipe join
    from sqlalchemy.orm import selectinload

    query = (
        select(CalendarMeal)
        .where(CalendarMeal.calendar_id == calendar_id)
        .options(selectinload(CalendarMeal.recipe))
    )

    if date_from:
        # Convert timezone-aware datetime to naive (UTC) for comparison
        date_from_naive = date_from.replace(tzinfo=None) if date_from.tzinfo else date_from
        query = query.where(CalendarMeal.meal_date >= date_from_naive)
    if date_to:
        # Convert timezone-aware datetime to naive (UTC) for comparison
        date_to_naive = date_to.replace(tzinfo=None) if date_to.tzinfo else date_to
        query = query.where(CalendarMeal.meal_date <= date_to_naive)

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    meals = result.scalars().all()

    # Convert to response format with recipe_name
    meal_responses = []
    for meal in meals:
        meal_dict = {
            "id": meal.id,
            "calendar_id": meal.calendar_id,
            "recipe_id": meal.recipe_id,
            "meal_date": meal.meal_date,
            "meal_type": meal.meal_type,
            "recipe_name": meal.recipe.title if meal.recipe else None,
            "created_at": meal.created_at,
        }
        meal_responses.append(CalendarMealResponse(**meal_dict))

    return meal_responses


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


@router.get("/{calendar_id}/export/ical")
async def export_calendar_to_ical(
    calendar_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export calendar to iCal format."""

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

    # Get all meals
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(CalendarMeal)
        .where(CalendarMeal.calendar_id == calendar_id)
        .options(selectinload(CalendarMeal.recipe))
    )
    meals = result.scalars().all()

    # Generate iCal content
    ical_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Meal Planner//EN",
        f"X-WR-CALNAME:{calendar.name}",
        "X-WR-TIMEZONE:UTC",
    ]

    for meal in meals:
        # Format datetime for iCal (must be in UTC)
        meal_dt = (
            meal.meal_date.replace(tzinfo=UTC) if meal.meal_date.tzinfo is None else meal.meal_date
        )
        dt_stamp = meal_dt.strftime("%Y%m%dT%H%M%SZ")

        # Generate a stable UID
        uid = f"meal-{meal.id}@mealplanner.local"

        ical_lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{dt_stamp}",
                f"DTSTART:{dt_stamp}",
                f"SUMMARY:{meal.meal_type.title()}: {meal.recipe.title if meal.recipe else 'Unknown Recipe'}",
                f"DESCRIPTION:{meal.recipe.description if meal.recipe and meal.recipe.description else ''}",
                "END:VEVENT",
            ]
        )

    ical_lines.append("END:VCALENDAR")

    ical_content = "\r\n".join(ical_lines)

    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'attachment; filename="{calendar.name.replace(" ", "_")}.ics"'
        },
    )


@router.post(
    "/{calendar_id}/prepopulate",
    response_model=CalendarPrepopulateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def prepopulate_calendar(
    calendar_id: int,
    prepopulate_data: CalendarPrepopulateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarPrepopulateResponse:
    """Prepopulate calendar with meals for a specified time period."""
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

    # Create prepopulate service
    service = CalendarPrepopulateService(db)

    try:
        # Prepopulate the calendar
        meals_created, end_date = await service.prepopulate_calendar(
            calendar_id=calendar_id,
            user=current_user,
            start_date=prepopulate_data.start_date,
            period=prepopulate_data.period,
            meal_types=prepopulate_data.meal_types,
            snacks_per_day=prepopulate_data.snacks_per_day,
            desserts_per_day=prepopulate_data.desserts_per_day,
            use_dietary_preferences=prepopulate_data.use_dietary_preferences,
            avoid_duplicates=prepopulate_data.avoid_duplicates,
        )

        return CalendarPrepopulateResponse(
            meals_created=meals_created,
            start_date=prepopulate_data.start_date,
            end_date=end_date,
            message=f"Successfully created {meals_created} meals for {prepopulate_data.period}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post(
    "/{calendar_id}/copy",
    response_model=CalendarCopyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def copy_calendar_period(
    calendar_id: int,
    copy_data: CalendarCopyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarCopyResponse:
    """Copy meals from one time period to another."""
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

    # Calculate source and target date ranges based on period
    source_start = copy_data.source_date.replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=None
    )
    target_start = copy_data.target_date.replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=None
    )

    if copy_data.period == "day":
        source_end = source_start + timedelta(days=1)
        target_end = target_start + timedelta(days=1)
    elif copy_data.period == "week":
        source_end = source_start + timedelta(days=7)
        target_end = target_start + timedelta(days=7)
    elif copy_data.period == "month":
        # Calculate days in the month
        if source_start.month == 12:
            next_month = source_start.replace(year=source_start.year + 1, month=1, day=1)
        else:
            next_month = source_start.replace(month=source_start.month + 1, day=1)
        source_end = next_month

        if target_start.month == 12:
            target_next_month = target_start.replace(year=target_start.year + 1, month=1, day=1)
        else:
            target_next_month = target_start.replace(month=target_start.month + 1, day=1)
        target_end = target_next_month
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid period. Must be 'day', 'week', or 'month'",
        )

    # Get source meals
    from sqlalchemy.orm import selectinload

    source_query = (
        select(CalendarMeal)
        .where(
            CalendarMeal.calendar_id == calendar_id,
            CalendarMeal.meal_date >= source_start,
            CalendarMeal.meal_date < source_end,
        )
        .options(selectinload(CalendarMeal.recipe))
    )
    result = await db.execute(source_query)
    source_meals = result.scalars().all()

    if not source_meals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No meals found in source {copy_data.period}",
        )

    # Get existing target meals if overwrite is False
    meals_skipped = 0
    if not copy_data.overwrite:
        target_query = select(CalendarMeal).where(
            CalendarMeal.calendar_id == calendar_id,
            CalendarMeal.meal_date >= target_start,
            CalendarMeal.meal_date < target_end,
        )
        result = await db.execute(target_query)
        existing_target_meals = result.scalars().all()

        # Create a set of (date, meal_type) tuples for quick lookup
        existing_slots = {(meal.meal_date.date(), meal.meal_type) for meal in existing_target_meals}
    else:
        # If overwrite is True, delete existing meals in target range
        delete_query = select(CalendarMeal).where(
            CalendarMeal.calendar_id == calendar_id,
            CalendarMeal.meal_date >= target_start,
            CalendarMeal.meal_date < target_end,
        )
        result = await db.execute(delete_query)
        meals_to_delete = result.scalars().all()
        for meal in meals_to_delete:
            await db.delete(meal)
        existing_slots = set()

    # Copy meals to target period
    meals_copied = 0
    for source_meal in source_meals:
        # Calculate offset from source_start
        time_offset = source_meal.meal_date - source_start

        # Apply same offset to target_start
        new_meal_date = target_start + time_offset

        # Skip if not overwriting and slot is occupied
        if not copy_data.overwrite:
            if (new_meal_date.date(), source_meal.meal_type) in existing_slots:
                meals_skipped += 1
                continue

        # Create new meal
        new_meal = CalendarMeal(
            calendar_id=calendar_id,
            recipe_id=source_meal.recipe_id,
            meal_date=new_meal_date,
            meal_type=source_meal.meal_type,
        )
        db.add(new_meal)
        meals_copied += 1

    await db.commit()

    return CalendarCopyResponse(
        meals_copied=meals_copied,
        meals_skipped=meals_skipped,
        source_start=source_start,
        source_end=source_end,
        target_start=target_start,
        target_end=target_end,
        message=f"Successfully copied {meals_copied} meals from {copy_data.period}. {meals_skipped} meals skipped.",
    )
