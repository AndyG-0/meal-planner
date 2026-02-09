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
    force_password_change: bool = False
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


class AdminPasswordReset(BaseModel):
    """Admin password reset schema."""

    temporary_password: str = Field(..., min_length=8)
    send_email: bool = True  # Whether to send email with temporary password


class PasswordResetConfig(BaseModel):
    """Password reset configuration schema."""

    email_enabled: bool
    admin_email: str


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
    email: str | None = None

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
    collection_id: int | None = Field(
        default=None, description="Optional collection ID to limit recipes to collection"
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
    user: UserBasic | None = None
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
    # Kroger product correlation
    kroger_product_id: str | None = None
    kroger_upc: str | None = None
    kroger_price: float | None = None
    kroger_product_name: str | None = None


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


# Email Settings Schemas
class EmailSettingsBase(BaseModel):
    """Base email settings schema."""

    sendgrid_api_key: str | None = None
    admin_email: str = Field(default="admin@mealplanner.local", max_length=255)


class EmailSettingsUpdate(BaseModel):
    """Email settings update schema."""

    sendgrid_api_key: str | None = None
    admin_email: str | None = Field(None, max_length=255)


class EmailSettingsResponse(BaseModel):
    """Email settings response schema (without API key)."""

    id: int
    admin_email: str
    updated_at: datetime | None = None
    has_sendgrid_key: bool = False

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


# Kroger Settings Schemas
class KrogerSettingsBase(BaseModel):
    """Base Kroger settings schema."""

    client_id: str | None = None
    client_secret: str | None = None
    oauth_client_id: str | None = None
    oauth_client_secret: str | None = None
    redirect_uri: str | None = None
    base_url: str = Field(default="https://api.kroger.com", max_length=255)
    environment: str = Field(default="production", pattern="^(production|certification)$")
    checkout_url: str | None = Field(None, max_length=500)
    certification_checkout_url: str | None = Field(None, max_length=500)
    cart_url: str | None = Field(None, max_length=500)
    certification_cart_url: str | None = Field(None, max_length=500)


class KrogerSettingsUpdate(BaseModel):
    """Kroger settings update schema."""

    client_id: str | None = None
    client_secret: str | None = None
    oauth_client_id: str | None = None
    oauth_client_secret: str | None = None
    redirect_uri: str | None = None
    base_url: str | None = Field(None, max_length=255)
    environment: str | None = Field(None, pattern="^(production|certification)$")
    checkout_url: str | None = Field(None, max_length=500)
    certification_checkout_url: str | None = Field(None, max_length=500)
    cart_url: str | None = Field(None, max_length=500)
    certification_cart_url: str | None = Field(None, max_length=500)


class KrogerSettingsResponse(BaseModel):
    """Kroger settings response schema (without secrets)."""

    id: int
    redirect_uri: str | None = None
    base_url: str
    environment: str
    checkout_url: str | None = None
    certification_checkout_url: str | None = None
    cart_url: str | None = None
    certification_cart_url: str | None = None
    updated_at: datetime | None = None
    has_client_credentials: bool = False
    has_oauth_credentials: bool = False

    model_config = {"from_attributes": True}


# Kroger Brand URLs Schemas
class KrogerBrandUrlsBase(BaseModel):
    """Base Kroger brand URLs schema."""

    brand: str = Field(..., max_length=100)
    display_name: str = Field(..., max_length=100)
    cart_url: str | None = Field(None, max_length=500)
    checkout_url: str | None = Field(None, max_length=500)
    certification_cart_url: str | None = Field(None, max_length=500)
    certification_checkout_url: str | None = Field(None, max_length=500)
    is_active: bool = True


class KrogerBrandUrlsCreate(KrogerBrandUrlsBase):
    """Kroger brand URLs creation schema."""


class KrogerBrandUrlsUpdate(BaseModel):
    """Kroger brand URLs update schema."""

    display_name: str | None = Field(None, max_length=100)
    cart_url: str | None = Field(None, max_length=500)
    checkout_url: str | None = Field(None, max_length=500)
    certification_cart_url: str | None = Field(None, max_length=500)
    certification_checkout_url: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class KrogerBrandUrlsResponse(KrogerBrandUrlsBase):
    """Kroger brand URLs response schema."""

    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# Kroger User Location Schemas
class KrogerLocationBase(BaseModel):
    """Base Kroger location schema."""

    location_id: str = Field(..., max_length=20)
    location_name: str = Field(..., max_length=255)
    location_address: str | None = Field(None, max_length=500)
    location_chain: str | None = Field(None, max_length=100)
    location_data: dict[str, Any] | None = None


class KrogerLocationCreate(KrogerLocationBase):
    """Kroger location creation schema."""


class KrogerLocationResponse(KrogerLocationBase):
    """Kroger location response schema."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# Kroger Auth Schemas
class KrogerAuthCallbackRequest(BaseModel):
    """Kroger OAuth2 callback request schema."""

    code: str
    state: str | None = None


class KrogerAuthResponse(BaseModel):
    """Kroger auth response schema."""

    authenticated: bool
    kroger_user_id: str | None = None
    kroger_email: str | None = None
    kroger_name: str | None = None
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}


# Kroger Product Search Schemas
class KrogerProductSearchRequest(BaseModel):
    """Kroger product search request schema."""

    term: str = Field(..., min_length=1, max_length=200)
    location_id: str = Field(..., max_length=20)
    fulfillment: str = Field(default="PICKUP", pattern="^(PICKUP|DELIVERY)$")
    limit: int = Field(default=20, ge=1, le=50)


class KrogerProductResponse(BaseModel):
    """Kroger product response schema."""

    product_id: str
    upc: str | None = None
    brand: str | None = None
    description: str
    size: str | None = None
    price: float | None = None
    regular_price: float | None = None
    on_sale: bool = False
    image_url: str | None = None
    categories: list[str] = []
    aisle_locations: list[dict[str, Any]] = []


class KrogerProductSearchResponse(BaseModel):
    """Kroger product search response schema."""

    products: list[KrogerProductResponse]
    total: int
    has_more: bool = False


# Kroger Location Search Schemas
class KrogerLocationSearchRequest(BaseModel):
    """Kroger location search request schema."""

    zip_code: str | None = Field(None, max_length=10)
    lat_long: str | None = None
    radius_in_miles: int = Field(default=10, ge=1, le=100)
    limit: int = Field(default=10, ge=1, le=200)
    chain: str | None = None


class KrogerStoreLocationResponse(BaseModel):
    """Kroger store location response schema."""

    location_id: str
    name: str
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    phone: str | None = None
    chain: str | None = None
    distance: float | None = None
    hours: dict[str, Any] | None = None
    departments: list[str] = []


class KrogerLocationSearchResponse(BaseModel):
    """Kroger location search response schema."""

    locations: list[KrogerStoreLocationResponse]
    total: int


# Kroger Cart Schemas
class KrogerCartItem(BaseModel):
    """Kroger cart item schema."""

    upc: str
    quantity: int = Field(default=1, ge=1)
    modality: str = Field(default="INSTORE", pattern="^(INSTORE|PICKUP|DELIVERY|SHIP)$")


class KrogerAddToCartRequest(BaseModel):
    """Kroger add to cart request schema."""

    items: list[KrogerCartItem]


class KrogerAddToCartResponse(BaseModel):
    """Kroger add to cart response schema."""

    success: bool
    message: str
    items_added: int = 0


class KrogerCartResponse(BaseModel):
    """Kroger cart response schema."""

    cart_id: str | None = None
    items: list[dict[str, Any]] = []
    total_quantity: int = 0
    estimated_total: float | None = None
    last_modified: datetime | None = None

    model_config = {"from_attributes": True}


# In-App Kroger Cart Schemas
class KrogerAppCartItem(BaseModel):
    """In-app Kroger cart item schema."""

    product_id: str
    upc: str
    product_name: str
    brand: str | None = None
    size: str | None = None
    price: float | None = None
    image_url: str | None = None
    quantity: int = Field(default=1, ge=1)
    fulfillment_type: str = Field(default="PICKUP", pattern="^(PICKUP|DELIVERY)$")
    grocery_list_item_name: str | None = None


class KrogerAppCartItemCreate(BaseModel):
    """Schema for adding items to in-app cart."""

    product_id: str
    upc: str
    product_name: str
    brand: str | None = None
    size: str | None = None
    price: float | None = None
    image_url: str | None = None
    quantity: int = Field(default=1, ge=1)
    fulfillment_type: str = Field(default="PICKUP", pattern="^(PICKUP|DELIVERY)$")
    grocery_list_item_name: str | None = None


class KrogerAppCartItemUpdate(BaseModel):
    """Schema for updating cart items."""

    quantity: int | None = Field(None, ge=1)
    fulfillment_type: str | None = Field(None, pattern="^(PICKUP|DELIVERY)$")


class KrogerAppCartItemResponse(BaseModel):
    """In-app cart item response schema."""

    id: int
    user_id: int
    product_id: str
    upc: str
    product_name: str
    brand: str | None = None
    size: str | None = None
    price: float | None = None
    image_url: str | None = None
    quantity: int
    fulfillment_type: str
    grocery_list_item_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KrogerAppCartResponse(BaseModel):
    """In-app cart response schema."""

    items: list[KrogerAppCartItemResponse]
    total_items: int
    total_quantity: int
    estimated_total: float | None = None
    fulfillment_type: str


class KrogerSendToKrogerRequest(BaseModel):
    """Request to send in-app cart to Kroger."""

    confirmed: bool = Field(default=False)  # User must confirm they understand the limitations


class KrogerSendToKrogerResponse(BaseModel):
    """Response from sending cart to Kroger."""

    success: bool
    message: str
    items_sent: int
    errors: list[str] = []

