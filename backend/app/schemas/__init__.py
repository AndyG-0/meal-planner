"""Pydantic schemas for API validation."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.blocked_domain import (  # noqa: F401
    BlockedDomainCreate,
    BlockedDomainResponse,
)


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
    dietary_preferences: list[str] | None = None
    calorie_target: int | None = Field(None, gt=0)
    preferences: dict[str, Any] | None = None


class UserResponse(UserBase):
    """User response schema."""

    id: int
    is_admin: bool = False
    dietary_preferences: list[str] | None = None
    calorie_target: int | None = None
    preferences: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """User login schema."""

    username: str
    password: str


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""

    token: str
    new_password: str = Field(..., min_length=8)


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

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate ingredient name doesn't contain measurements."""
        if not v or not v.strip():
            raise ValueError("Ingredient name cannot be empty")

        # Check if name starts with a number or fraction (likely has measurement)
        v = v.strip()
        if v and (v[0].isdigit() or v.startswith("(")):
            raise ValueError(
                f'Ingredient name "{v}" appears to contain measurements. '
                "Please put measurements in quantity/unit fields only."
            )

        # Check for actual measurement units as standalone first words or second words
        # Only flag if they appear as measurement units (e.g., "1/2 tsp flour" or "tsp garlic")
        words = v.split()
        if len(words) > 0:
            first_word = words[0].lower()
            # Check if first word is a measurement unit (not just contains the letters)
            exact_measurement_units = [
                "tsp",
                "tbsp",
                "cup",
                "cups",
                "oz",
                "lb",
                "lbs",
                "g",
                "kg",
                "ml",
                "l",
                "qt",
                "gal",
                "pint",
                "quart",
            ]
            if first_word in exact_measurement_units:
                raise ValueError(
                    f'Ingredient name "{v}" appears to contain measurements. '
                    "Please put measurements in quantity/unit fields only."
                )

        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        """Validate quantity is non-negative (0 allowed for 'to taste' ingredients)."""
        if v < 0:
            raise ValueError("Ingredient quantity cannot be negative")
        return v

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        """Validate unit is not empty and warn about generic units."""
        if not v or not v.strip():
            raise ValueError("Ingredient unit cannot be empty")

        v = v.strip()
        # Warn about overly generic units
        if v.lower() == "serving" and v != "serving":
            # Normalize to lowercase
            v = "serving"

        return v


class RecipeBase(BaseModel):
    """Base recipe schema - now supports menu items with minimal fields."""

    title: str = Field(..., min_length=1, max_length=255)  # Only required field
    description: str | None = None
    ingredients: list[IngredientSchema] | None = None  # Optional for quick menu items
    instructions: list[str] | None = None  # Optional for quick menu items
    serving_size: int = 4
    prep_time: int | None = None
    cook_time: int | None = None
    difficulty: str | None = Field(None, pattern="^(easy|medium|hard)$")
    category: str | None = Field(
        None, pattern="^(breakfast|lunch|dinner|snack|dessert|staple|frozen)$"
    )
    nutritional_info: dict[str, Any] | None = None
    visibility: str = Field("private", pattern="^(private|group|public)$")
    group_id: int | None = None
    # Deprecated fields - kept for backward compatibility
    is_shared: bool = False
    is_public: bool = False

    @field_validator("ingredients", mode="before")
    @classmethod
    def convert_ingredients(cls, v):
        """Convert string ingredients to IngredientSchema objects."""
        if not v:
            return []

        result = []
        for item in v:
            # If already a dict/object, use it
            if isinstance(item, dict):
                result.append(item)
            # If it's a string, convert it to the expected format
            elif isinstance(item, str):
                # Try to parse simple format like "1 cup flour"
                parts = item.split(maxsplit=2)
                if len(parts) >= 3:
                    try:
                        quantity = float(parts[0])
                        unit = parts[1]
                        name = parts[2]
                    except ValueError:
                        # Can't parse quantity, use defaults
                        quantity = 1.0
                        unit = "serving"
                        name = item
                else:
                    # Can't parse, use defaults
                    quantity = 1.0
                    unit = "serving"
                    name = item

                result.append({"name": name, "quantity": quantity, "unit": unit})
            else:
                # Already an IngredientSchema object
                result.append(item)

        return result


class RecipeCreate(RecipeBase):
    """Recipe creation schema."""

    pass


class RecipeQuickAdd(BaseModel):
    """Quick-add menu item schema - minimal fields for rapid entry."""

    title: str = Field(..., min_length=1, max_length=255)
    category: str | None = Field(
        None, pattern="^(breakfast|lunch|dinner|snack|dessert|staple|frozen)$"
    )


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
    category: str | None = Field(
        None, pattern="^(breakfast|lunch|dinner|snack|dessert|staple|frozen)$"
    )
    nutritional_info: dict[str, Any] | None = None
    visibility: str | None = Field(None, pattern="^(private|group|public)$")
    group_id: int | None = None
    is_shared: bool | None = None
    is_public: bool | None = None


class RecipeResponse(RecipeBase):
    """Recipe response schema."""

    id: int
    owner_id: int
    image_url: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    is_favorite: bool = False
    tags: list["RecipeTagResponse"] = []

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


# Pagination Schemas
class PaginationMetadata(BaseModel):
    """Pagination metadata schema."""

    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedRecipeResponse(BaseModel):
    """Paginated recipe response with metadata."""

    items: list["RecipeResponse"]
    pagination: PaginationMetadata


# Recipe Rating Schemas
class UserBasic(BaseModel):
    """Basic user info for ratings/comments."""

    id: int
    username: str

    model_config = {"from_attributes": True}


class RecipeRatingCreate(BaseModel):
    """Recipe rating creation schema."""

    rating: int = Field(..., ge=1, le=5)
    review: str | None = None


class RecipeRatingResponse(RecipeRatingCreate):
    """Recipe rating response schema."""

    id: int
    recipe_id: int
    user_id: int
    user: UserBasic | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Calendar Schemas
class CalendarBase(BaseModel):
    """Base calendar schema."""

    name: str = Field(..., min_length=1, max_length=100)
    visibility: str = Field("private", pattern="^(private|group|public)$")
    group_id: int | None = None
    # Deprecated field - kept for backward compatibility
    is_shared: bool = False


class CalendarCreate(CalendarBase):
    """Calendar creation schema."""

    pass


class CalendarUpdate(BaseModel):
    """Calendar update schema."""

    name: str | None = Field(None, min_length=1, max_length=100)
    visibility: str | None = Field(None, pattern="^(private|group|public)$")
    group_id: int | None = None
    is_shared: bool | None = None


class CalendarResponse(CalendarBase):
    """Calendar response schema."""

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime | None = None
    can_edit: bool | None = Field(None, description="Whether the current user can edit this calendar")

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
    recipe_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CalendarPrepopulateRequest(BaseModel):
    """Calendar prepopulation request schema."""

    start_date: datetime
    period: str = Field(..., pattern="^(day|week|month)$", description="Time period to prepopulate")
    meal_types: list[str] = Field(..., description="Meal types to include")
    snacks_per_day: int = Field(default=0, ge=0, le=5, description="Number of snacks per day")
    desserts_per_day: int = Field(default=0, ge=0, le=3, description="Number of desserts per day")
    use_dietary_preferences: bool = Field(
        default=True, description="Filter recipes by dietary preferences"
    )
    avoid_duplicates: bool = Field(
        default=True, description="Try to avoid duplicate recipes when possible"
    )

    @field_validator("meal_types")
    @classmethod
    def validate_meal_types(cls, v: list[str]) -> list[str]:
        """Validate meal types."""
        valid_types = ["breakfast", "lunch", "dinner"]
        for meal_type in v:
            if meal_type not in valid_types:
                raise ValueError(f"Invalid meal type: {meal_type}. Must be one of {valid_types}")
        return v


class CalendarPrepopulateResponse(BaseModel):
    """Calendar prepopulation response schema."""

    meals_created: int
    start_date: datetime
    end_date: datetime
    message: str


class CalendarCopyRequest(BaseModel):
    """Calendar copy request schema."""

    source_date: datetime = Field(..., description="Source date to copy from")
    target_date: datetime = Field(..., description="Target date to copy to")
    period: str = Field(..., pattern="^(day|week|month)$", description="Time period to copy")
    overwrite: bool = Field(default=False, description="Whether to overwrite existing meals")


class CalendarCopyResponse(BaseModel):
    """Calendar copy response schema."""

    meals_copied: int
    meals_skipped: int
    source_start: datetime
    source_end: datetime
    target_start: datetime
    target_end: datetime
    message: str


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
    visibility: str = Field("private", pattern="^(private|group|public)$")
    group_id: int | None = None


class GroceryListResponse(BaseModel):
    """Grocery list response schema."""

    id: int
    user_id: int
    name: str
    date_from: datetime | None = None
    date_to: datetime | None = None
    items: list[GroceryListItem]
    visibility: str
    group_id: int | None = None
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


# Admin Schemas
class AdminUserUpdate(BaseModel):
    """Admin user update schema."""

    is_admin: bool | None = None
    email: EmailStr | None = None


class AdminStatsResponse(BaseModel):
    """Admin statistics response schema."""

    total_users: int
    total_recipes: int
    total_calendars: int
    total_groups: int
    total_public_recipes: int
    total_group_recipes: int
    total_private_recipes: int
    version: str


class AdminUserListResponse(BaseModel):
    """Admin user list item response schema."""

    id: int
    username: str
    email: str
    is_admin: bool
    created_at: datetime
    recipe_count: int = 0
    calendar_count: int = 0
    group_count: int = 0

    model_config = {"from_attributes": True}


# Feature Toggle Schemas
class FeatureToggleBase(BaseModel):
    """Base feature toggle schema."""

    feature_key: str = Field(..., max_length=100)
    feature_name: str = Field(..., max_length=255)
    description: str | None = None
    is_enabled: bool = False


class FeatureToggleCreate(FeatureToggleBase):
    """Feature toggle creation schema."""

    pass


class FeatureToggleUpdate(BaseModel):
    """Feature toggle update schema."""

    feature_name: str | None = Field(None, max_length=255)
    description: str | None = None
    is_enabled: bool | None = None


class FeatureToggleResponse(FeatureToggleBase):
    """Feature toggle response schema."""

    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# OpenAI Settings Schemas
class OpenAISettingsBase(BaseModel):
    """Base OpenAI settings schema."""

    api_key: str | None = None
    model: str = Field(default="gpt-4", max_length=100)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=100, le=4000)
    system_prompt: str | None = None


class OpenAISettingsUpdate(BaseModel):
    """OpenAI settings update schema."""

    api_key: str | None = None
    model: str | None = Field(None, max_length=100)
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=100, le=4000)
    system_prompt: str | None = None
    searxng_url: str | None = None  # SEARXNG URL


class OpenAISettingsResponse(BaseModel):
    """OpenAI settings response schema (without API key)."""

    id: int
    model: str
    temperature: float
    max_tokens: int
    system_prompt: str | None = None
    searxng_url: str = "http://localhost:8085"  # SEARXNG URL
    updated_at: datetime | None = None
    has_api_key: bool = False

    model_config = {"from_attributes": True}


# Session Settings Schemas
class SessionSettingsBase(BaseModel):
    """Base session settings schema."""

    session_ttl_value: int = Field(default=90, ge=1, le=365)
    session_ttl_unit: str = Field(default="days", pattern="^(minutes|hours|days)$")


class SessionSettingsUpdate(BaseModel):
    """Session settings update schema."""

    session_ttl_value: int | None = Field(None, ge=1, le=365)
    session_ttl_unit: str | None = Field(None, pattern="^(minutes|hours|days)$")


class SessionSettingsResponse(BaseModel):
    """Session settings response schema."""

    id: int
    session_ttl_value: int
    session_ttl_unit: str
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# AI Chat Schemas
class AIChatMessage(BaseModel):
    """AI chat message schema."""

    role: str = Field(..., pattern="^(user|assistant|system|tool)$")
    content: str | None  # Can be None for assistant messages with tool_calls
    tool_call_id: str | None = None  # Required for tool role messages
    tool_calls: list[dict[str, Any]] | None = None  # For assistant messages with tool calls


class AIChatRequest(BaseModel):
    """AI chat request schema."""

    messages: list[AIChatMessage]
    use_dietary_preferences: bool = True  # Toggle for using dietary preferences


class AIChatResponse(BaseModel):
    """AI chat response schema."""

    message: str
    tool_calls: list[dict[str, Any]] | None = None


class AIRecipeValidation(BaseModel):
    """AI recipe validation schema for user confirmation."""

    action: str = Field(..., pattern="^(create|update)$")
    recipe_data: dict[str, Any]
    confirmation_message: str


# OpenAI Models Schemas
class OpenAIModelInfo(BaseModel):
    """OpenAI model information schema."""

    id: str
    owned_by: str
    created: int | None = None


class OpenAIModelsListResponse(BaseModel):
    """OpenAI models list response schema."""

    models: list[OpenAIModelInfo]


# Recipe Collection Schemas
class RecipeCollectionCreate(BaseModel):
    """Recipe collection creation schema."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class RecipeCollectionUpdate(BaseModel):
    """Recipe collection update schema."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None


class RecipeCollectionItemResponse(BaseModel):
    """Recipe collection item schema with basic recipe info."""

    id: int
    recipe_id: int
    recipe_title: str | None = None
    recipe_category: str | None = None
    added_at: datetime

    model_config = {"from_attributes": True}


class RecipeCollectionResponse(BaseModel):
    """Recipe collection response schema."""

    id: int
    name: str
    description: str | None = None
    user_id: int
    created_at: datetime
    updated_at: datetime | None = None
    items: list["RecipeCollectionItemResponse"] = []

    model_config = {"from_attributes": True}


# Recipe Ingredient Schemas
class RecipeIngredientBase(BaseModel):
    """Base recipe ingredient schema."""

    ingredient_recipe_id: int | None = None  # For staple recipes
    ingredient_name: str | None = None  # For regular ingredients
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)
    notes: str | None = None

    @field_validator("ingredient_name")
    @classmethod
    def validate_ingredient_source(cls, v, info):
        """Ensure either ingredient_recipe_id or ingredient_name is provided."""
        ingredient_recipe_id = info.data.get("ingredient_recipe_id")
        if not ingredient_recipe_id and not v:
            raise ValueError("Either ingredient_recipe_id or ingredient_name must be provided")
        return v


class RecipeIngredientCreate(RecipeIngredientBase):
    """Recipe ingredient creation schema."""

    pass


class RecipeIngredientUpdate(BaseModel):
    """Recipe ingredient update schema."""

    ingredient_recipe_id: int | None = None
    ingredient_name: str | None = None
    quantity: float | None = Field(None, gt=0)
    unit: str | None = Field(None, min_length=1)
    notes: str | None = None


class RecipeIngredientResponse(RecipeIngredientBase):
    """Recipe ingredient response schema."""

    id: int
    recipe_id: int
    # Include recipe details if it's a staple recipe
    ingredient_recipe: "RecipeResponse | None" = None

    model_config = {"from_attributes": True}
