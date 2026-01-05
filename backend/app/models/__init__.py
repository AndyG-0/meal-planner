"""Database models."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    dietary_preferences = Column(JSON)  # List of preferences: vegan, vegetarian, keto, etc.
    calorie_target = Column(Integer)  # Daily calorie target
    preferences = Column(
        JSON
    )  # Other user preferences: {calendar_start_day: 'monday', theme: 'dark'}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    recipes = relationship("Recipe", back_populates="owner", foreign_keys="Recipe.owner_id")
    favorites = relationship("UserFavorite", back_populates="user")
    ratings = relationship("RecipeRating", back_populates="user")
    calendars = relationship("Calendar", back_populates="owner", foreign_keys="Calendar.owner_id")
    groups_owned = relationship("Group", back_populates="owner", foreign_keys="Group.owner_id")
    group_memberships = relationship("GroupMember", back_populates="user")
    grocery_lists = relationship("GroceryList", back_populates="user")
    pantry_items = relationship("PantryInventory", back_populates="user")


class Recipe(Base):
    """Recipe model."""

    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ingredients = Column(JSON, nullable=False)  # List of {name, quantity, unit}
    instructions = Column(JSON, nullable=False)  # List of steps
    image_url = Column(String(500))
    serving_size = Column(Integer, default=4)
    prep_time = Column(Integer)  # minutes
    cook_time = Column(Integer)  # minutes
    difficulty = Column(String(20))  # easy, medium, hard
    category = Column(String(50))  # breakfast, lunch, dinner, snack, dessert, staple, frozen
    nutritional_info = Column(JSON)  # {calories, protein, carbs, fat, allergens}
    visibility = Column(String(20), default="private", nullable=False)  # private, group, public
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    # Deprecated fields - kept for backward compatibility
    is_shared = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="recipes", foreign_keys=[owner_id])
    group = relationship("Group", back_populates="recipes", foreign_keys=[group_id])
    tags = relationship("RecipeTag", back_populates="recipe", cascade="all, delete-orphan")
    ratings = relationship("RecipeRating", back_populates="recipe", cascade="all, delete-orphan")
    favorites = relationship("UserFavorite", back_populates="recipe", cascade="all, delete-orphan")
    calendar_meals = relationship("CalendarMeal", back_populates="recipe")
    recipe_ingredients = relationship(
        "RecipeIngredient",
        back_populates="recipe",
        foreign_keys="RecipeIngredient.recipe_id",
        cascade="all, delete-orphan",
    )
    used_in_recipes = relationship(
        "RecipeIngredient",
        back_populates="ingredient_recipe",
        foreign_keys="RecipeIngredient.ingredient_recipe_id",
    )


class RecipeIngredient(Base):
    """Recipe ingredient model - supports both regular ingredients and staple recipes."""

    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(
        Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Either ingredient_recipe_id (for staple recipes) or ingredient_name (for regular ingredients)
    ingredient_recipe_id = Column(
        Integer, ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    ingredient_name = Column(String(255), nullable=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)  # e.g., "softened", "chopped", etc.

    # Relationships
    recipe = relationship("Recipe", back_populates="recipe_ingredients", foreign_keys=[recipe_id])
    ingredient_recipe = relationship(
        "Recipe", back_populates="used_in_recipes", foreign_keys=[ingredient_recipe_id]
    )


class RecipeTag(Base):
    """Recipe tag model."""

    __tablename__ = "recipe_tags"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    tag_name = Column(String(50), nullable=False)
    tag_category = Column(String(50))  # dietary, meal_type, cuisine, etc.

    # Relationships
    recipe = relationship("Recipe", back_populates="tags")

    __table_args__ = (UniqueConstraint("recipe_id", "tag_name", name="uq_recipe_tag"),)


class RecipeRating(Base):
    """Recipe rating model."""

    __tablename__ = "recipe_ratings"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    review = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    recipe = relationship("Recipe", back_populates="ratings")
    user = relationship("User", back_populates="ratings")

    __table_args__ = (UniqueConstraint("recipe_id", "user_id", name="uq_recipe_user_rating"),)


class UserFavorite(Base):
    """User favorite recipe model."""

    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="favorites")
    recipe = relationship("Recipe", back_populates="favorites")

    __table_args__ = (UniqueConstraint("user_id", "recipe_id", name="uq_user_favorite"),)


class Calendar(Base):
    """Calendar model."""

    __tablename__ = "calendars"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    visibility = Column(String(20), default="private", nullable=False)  # private, group, public
    # Deprecated field - kept for backward compatibility
    is_shared = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="calendars", foreign_keys=[owner_id])
    group = relationship("Group", back_populates="calendars")
    meals = relationship("CalendarMeal", back_populates="calendar", cascade="all, delete-orphan")


class CalendarMeal(Base):
    """Calendar meal assignment model."""

    __tablename__ = "calendar_meals"

    id = Column(Integer, primary_key=True, index=True)
    calendar_id = Column(Integer, ForeignKey("calendars.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    meal_date = Column(DateTime, nullable=False)
    meal_type = Column(String(20), nullable=False)  # breakfast, lunch, dinner, snack
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    calendar = relationship("Calendar", back_populates="meals")
    recipe = relationship("Recipe", back_populates="calendar_meals")


class Group(Base):
    """Group model for sharing."""

    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="groups_owned", foreign_keys=[owner_id])
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    calendars = relationship("Calendar", back_populates="group")
    recipes = relationship("Recipe", back_populates="group", foreign_keys="Recipe.group_id")
    grocery_lists = relationship("GroceryList", back_populates="group")


class GroupMember(Base):
    """Group member model."""

    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member")  # admin, member
    permissions = Column(JSON)  # {can_edit: bool, can_view: bool}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")

    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_member"),)


class GroceryList(Base):
    """Grocery list model."""

    __tablename__ = "grocery_lists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    date_from = Column(DateTime)
    date_to = Column(DateTime)
    items = Column(JSON, nullable=False)  # List of consolidated items
    visibility = Column(String(20), default="private", nullable=False)  # private, group, public
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="grocery_lists")
    group = relationship("Group", back_populates="grocery_lists")


class PantryInventory(Base):
    """Pantry inventory model."""

    __tablename__ = "pantry_inventory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ingredient_name = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="pantry_items")

    __table_args__ = (UniqueConstraint("user_id", "ingredient_name", name="uq_user_ingredient"),)


class FeatureToggle(Base):
    """Feature toggle model for managing feature flags."""

    __tablename__ = "feature_toggles"

    id = Column(Integer, primary_key=True, index=True)
    feature_key = Column(String(100), unique=True, nullable=False, index=True)
    feature_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_enabled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OpenAISettings(Base):
    """OpenAI settings model for AI integration configuration."""

    __tablename__ = "openai_settings"

    id = Column(Integer, primary_key=True)
    api_key = Column(String(255), nullable=True)
    model = Column(String(100), default="gpt-4", nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    max_tokens = Column(Integer, default=2000, nullable=False)
    system_prompt = Column(Text, nullable=True)
    searxng_url = Column(String(255), default="http://localhost:8085")  # SEARXNG URL
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SessionSettings(Base):
    """Session settings model for configurable session TTL."""

    __tablename__ = "session_settings"

    id = Column(Integer, primary_key=True)
    session_ttl_value = Column(Integer, default=90, nullable=False)  # Numeric value
    session_ttl_unit = Column(String(20), default="days", nullable=False)  # minutes, hours, or days
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PasswordResetToken(Base):
    """Password reset token model."""

    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User")


class RecipeCollection(Base):
    """Recipe collection model for organizing recipes."""

    __tablename__ = "recipe_collections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")
    items = relationship(
        "RecipeCollectionItem", back_populates="collection", cascade="all, delete-orphan"
    )


class RecipeCollectionItem(Base):
    """Recipe collection item model for many-to-many relationship."""

    __tablename__ = "recipe_collection_items"

    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("recipe_collections.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    collection = relationship("RecipeCollection", back_populates="items")
    recipe = relationship("Recipe")

    __table_args__ = (UniqueConstraint("collection_id", "recipe_id", name="uq_collection_recipe"),)
