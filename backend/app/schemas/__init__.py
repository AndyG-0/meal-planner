"""Pydantic schemas for API validation."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """User update schema."""

    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8)


class UserResponse(UserBase):
    """User response schema."""

    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """User login schema."""

    username: str
    password: str


# Token Schemas
class Token(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""

    user_id: int | None = None


# Recipe Schemas
class IngredientSchema(BaseModel):
    """Ingredient schema."""

    name: str
    quantity: float
    unit: str


class RecipeBase(BaseModel):
    """Base recipe schema."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    ingredients: list[IngredientSchema]
    instructions: list[str]
    serving_size: int = 4
    prep_time: int | None = None
    cook_time: int | None = None
    difficulty: str | None = Field(None, pattern="^(easy|medium|hard)$")
    nutritional_info: dict[str, Any] | None = None
    is_shared: bool = False
    is_public: bool = False


class RecipeCreate(RecipeBase):
    """Recipe creation schema."""

    pass


class RecipeUpdate(BaseModel):
    """Recipe update schema."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    ingredients: list[IngredientSchema] | None = None
    instructions: list[str] | None = None
    serving_size: int | None = None
    prep_time: int | None = None
    cook_time: int | None = None
    difficulty: str | None = Field(None, pattern="^(easy|medium|hard)$")
    nutritional_info: dict[str, Any] | None = None
    is_shared: bool | None = None
    is_public: bool | None = None


class RecipeResponse(RecipeBase):
    """Recipe response schema."""

    id: int
    owner_id: int
    image_url: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# Recipe Tag Schemas
class RecipeTagCreate(BaseModel):
    """Recipe tag creation schema."""

    tag_name: str = Field(..., min_length=1, max_length=50)
    tag_category: str | None = Field(None, max_length=50)


class RecipeTagResponse(RecipeTagCreate):
    """Recipe tag response schema."""

    id: int
    recipe_id: int

    model_config = {"from_attributes": True}


# Recipe Rating Schemas
class RecipeRatingCreate(BaseModel):
    """Recipe rating creation schema."""

    rating: int = Field(..., ge=1, le=5)
    review: str | None = None


class RecipeRatingResponse(RecipeRatingCreate):
    """Recipe rating response schema."""

    id: int
    recipe_id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# Calendar Schemas
class CalendarBase(BaseModel):
    """Base calendar schema."""

    name: str = Field(..., min_length=1, max_length=100)
    is_shared: bool = False
    group_id: int | None = None


class CalendarCreate(CalendarBase):
    """Calendar creation schema."""

    pass


class CalendarUpdate(BaseModel):
    """Calendar update schema."""

    name: str | None = Field(None, min_length=1, max_length=100)
    is_shared: bool | None = None


class CalendarResponse(CalendarBase):
    """Calendar response schema."""

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# Calendar Meal Schemas
class CalendarMealCreate(BaseModel):
    """Calendar meal creation schema."""

    recipe_id: int
    meal_date: datetime
    meal_type: str = Field(..., pattern="^(breakfast|lunch|dinner|snack)$")


class CalendarMealResponse(CalendarMealCreate):
    """Calendar meal response schema."""

    id: int
    calendar_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# Group Schemas
class GroupBase(BaseModel):
    """Base group schema."""

    name: str = Field(..., min_length=1, max_length=100)


class GroupCreate(GroupBase):
    """Group creation schema."""

    pass


class GroupUpdate(BaseModel):
    """Group update schema."""

    name: str | None = Field(None, min_length=1, max_length=100)


class GroupResponse(GroupBase):
    """Group response schema."""

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# Group Member Schemas
class GroupMemberCreate(BaseModel):
    """Group member creation schema."""

    user_id: int
    role: str = "member"
    permissions: dict[str, bool] | None = None


class GroupMemberResponse(GroupMemberCreate):
    """Group member response schema."""

    id: int
    group_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# Grocery List Schemas
class GroceryListItem(BaseModel):
    """Grocery list item schema."""

    name: str
    quantity: float
    unit: str
    category: str | None = None
    checked: bool = False


class GroceryListCreate(BaseModel):
    """Grocery list creation schema."""

    name: str = Field(..., min_length=1, max_length=100)
    date_from: datetime | None = None
    date_to: datetime | None = None


class GroceryListResponse(BaseModel):
    """Grocery list response schema."""

    id: int
    user_id: int
    name: str
    date_from: datetime | None = None
    date_to: datetime | None = None
    items: list[GroceryListItem]
    created_at: datetime

    model_config = {"from_attributes": True}


# Pantry Inventory Schemas
class PantryInventoryCreate(BaseModel):
    """Pantry inventory creation schema."""

    ingredient_name: str = Field(..., min_length=1, max_length=100)
    quantity: float = Field(..., gt=0)
    unit: str | None = Field(None, max_length=50)


class PantryInventoryUpdate(BaseModel):
    """Pantry inventory update schema."""

    quantity: float = Field(..., gt=0)
    unit: str | None = Field(None, max_length=50)


class PantryInventoryResponse(PantryInventoryCreate):
    """Pantry inventory response schema."""

    id: int
    user_id: int
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
