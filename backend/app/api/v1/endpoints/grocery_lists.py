"""Grocery list endpoints."""

import csv
import logging
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user
from app.database import get_db
from app.models import Calendar, CalendarMeal, GroceryList, Recipe, User
from app.schemas import GroceryListCreate, GroceryListResponse

logger = logging.getLogger(__name__)
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

    # Get meals in date range
    query = select(CalendarMeal).where(CalendarMeal.calendar_id == calendar_id)

    if list_data.date_from:
        # Convert timezone-aware datetime to naive (UTC) for comparison
        date_from_naive = (
            list_data.date_from.replace(tzinfo=None)
            if list_data.date_from.tzinfo
            else list_data.date_from
        )
        query = query.where(CalendarMeal.meal_date >= date_from_naive)
    if list_data.date_to:
        # Convert timezone-aware datetime to naive (UTC) for comparison
        date_to_naive = (
            list_data.date_to.replace(tzinfo=None)
            if list_data.date_to.tzinfo
            else list_data.date_to
        )
        query = query.where(CalendarMeal.meal_date <= date_to_naive)

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
    # Convert timezone-aware datetimes to naive (UTC) for storage
    date_from_naive = (
        list_data.date_from.replace(tzinfo=None)
        if list_data.date_from and list_data.date_from.tzinfo
        else list_data.date_from
    )
    date_to_naive = (
        list_data.date_to.replace(tzinfo=None)
        if list_data.date_to and list_data.date_to.tzinfo
        else list_data.date_to
    )

    grocery_list = GroceryList(
        user_id=current_user.id,
        name=list_data.name,
        date_from=date_from_naive,
        date_to=date_to_naive,
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
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[GroceryList]:
    """List user's grocery lists with pagination."""
    result = await db.execute(
        select(GroceryList).where(GroceryList.user_id == current_user.id).offset(skip).limit(limit)
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
    result = await db.execute(select(GroceryList).where(GroceryList.id == list_id))
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
    result = await db.execute(select(GroceryList).where(GroceryList.id == list_id))
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


@router.patch("/{list_id}", response_model=GroceryListResponse)
async def update_grocery_list(
    list_id: int,
    items: list[dict],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> GroceryList:
    """Update grocery list items (add, remove, check/uncheck)."""
    result = await db.execute(select(GroceryList).where(GroceryList.id == list_id))
    grocery_list = result.scalar_one_or_none()

    if not grocery_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grocery list not found",
        )

    if grocery_list.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this grocery list",
        )

    # Update items
    grocery_list.items = items
    await db.commit()
    await db.refresh(grocery_list)

    return grocery_list


@router.get("/{list_id}/export/csv")
async def export_grocery_list_csv(
    list_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export grocery list as CSV file."""
    result = await db.execute(select(GroceryList).where(GroceryList.id == list_id))
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

    # Create CSV
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["Item", "Quantity", "Unit", "Category", "Checked"])

    # Group items by category
    items_by_category = {}
    for item in grocery_list.items:
        category = item.get("category", "Other")
        if category not in items_by_category:
            items_by_category[category] = []
        items_by_category[category].append(item)

    # Write items grouped by category
    for category in sorted(items_by_category.keys()):
        for item in items_by_category[category]:
            writer.writerow(
                [
                    item["name"],
                    item["quantity"],
                    item["unit"],
                    category,
                    "✓" if item.get("checked", False) else "",
                ]
            )

    output.seek(0)

    # Generate filename
    filename = f"{grocery_list.name.replace(' ', '_')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{list_id}/export/txt")
async def export_grocery_list_txt(
    list_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export grocery list as text file."""
    result = await db.execute(select(GroceryList).where(GroceryList.id == list_id))
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

    # Create text content
    lines = []
    lines.append(f"Grocery List: {grocery_list.name}")
    lines.append("=" * 50)

    if grocery_list.date_from and grocery_list.date_to:
        lines.append(
            f"Period: {grocery_list.date_from.strftime('%Y-%m-%d')} to {grocery_list.date_to.strftime('%Y-%m-%d')}"
        )
        lines.append("")

    # Group items by category
    items_by_category = {}
    for item in grocery_list.items:
        category = item.get("category", "Other")
        if category not in items_by_category:
            items_by_category[category] = []
        items_by_category[category].append(item)

    # Write items grouped by category
    for category in sorted(items_by_category.keys()):
        lines.append(f"\n{category}:")
        lines.append("-" * 30)
        for item in items_by_category[category]:
            check_mark = "[✓] " if item.get("checked", False) else "[ ] "
            lines.append(f"{check_mark}{item['name']} - {item['quantity']} {item['unit']}")

    content = "\n".join(lines)

    # Generate filename
    filename = f"{grocery_list.name.replace(' ', '_')}.txt"

    return StreamingResponse(
        iter([content]),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{list_id}/print", response_class=HTMLResponse)
async def print_grocery_list(
    list_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Generate printer-friendly HTML view of grocery list."""
    result = await db.execute(select(GroceryList).where(GroceryList.id == list_id))
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

    # Group items by category
    items_by_category = {}
    for item in grocery_list.items:
        category = item.get("category", "Other")
        if category not in items_by_category:
            items_by_category[category] = []
        items_by_category[category].append(item)

    # Generate HTML
    html_parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='UTF-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        f"<title>{grocery_list.name}</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }",
        "h1 { border-bottom: 3px solid #333; padding-bottom: 10px; }",
        ".date-range { color: #666; margin-bottom: 20px; font-style: italic; }",
        ".category { margin-top: 30px; page-break-inside: avoid; }",
        ".category h2 { background-color: #f0f0f0; padding: 8px; border-left: 4px solid #333; }",
        ".item { padding: 8px 0; border-bottom: 1px solid #eee; display: flex; align-items: center; }",
        ".checkbox { width: 20px; height: 20px; border: 2px solid #333; margin-right: 15px; flex-shrink: 0; }",
        ".checkbox.checked { background-color: #333; position: relative; }",
        ".checkbox.checked::after { content: '✓'; color: white; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }",
        ".item-name { flex: 1; font-weight: 500; }",
        ".item-quantity { color: #666; margin-left: 10px; white-space: nowrap; }",
        ".item.checked { opacity: 0.5; text-decoration: line-through; }",
        "@media print {",
        "  body { padding: 0; }",
        "  .no-print { display: none; }",
        "  .category { page-break-inside: avoid; }",
        "}",
        ".print-button { margin: 20px 0; padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }",
        ".print-button:hover { background-color: #0056b3; }",
        "</style>",
        "<script>",
        "function printPage() { window.print(); }",
        "</script>",
        "</head>",
        "<body>",
        "<button class='print-button no-print' onclick='printPage()'>Print This List</button>",
        f"<h1>{grocery_list.name}</h1>",
    ]

    if grocery_list.date_from and grocery_list.date_to:
        html_parts.append(
            f"<div class='date-range'>Period: {grocery_list.date_from.strftime('%B %d, %Y')} - {grocery_list.date_to.strftime('%B %d, %Y')}</div>"
        )

    # Add items by category
    for category in sorted(items_by_category.keys()):
        html_parts.append("<div class='category'>")
        html_parts.append(f"<h2>{category}</h2>")

        for item in items_by_category[category]:
            checked = item.get("checked", False)
            checked_class = " checked" if checked else ""
            checkbox_class = "checkbox" + (" checked" if checked else "")

            html_parts.append(f"<div class='item{checked_class}'>")
            html_parts.append(f"<div class='{checkbox_class}'></div>")
            html_parts.append(f"<div class='item-name'>{item['name']}</div>")
            html_parts.append(f"<div class='item-quantity'>{item['quantity']} {item['unit']}</div>")
            html_parts.append("</div>")

        html_parts.append("</div>")

    html_parts.append("</body>")
    html_parts.append("</html>")

    return "\n".join(html_parts)
