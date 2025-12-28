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
    nutritional_info = Column(JSON)  # {calories, protein, carbs, fat, allergens}
    is_shared = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="recipes", foreign_keys=[owner_id])
    tags = relationship("RecipeTag", back_populates="recipe", cascade="all, delete-orphan")
    ratings = relationship("RecipeRating", back_populates="recipe", cascade="all, delete-orphan")
    favorites = relationship("UserFavorite", back_populates="recipe", cascade="all, delete-orphan")
    calendar_meals = relationship("CalendarMeal", back_populates="recipe")


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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="grocery_lists")


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

    __table_args__ = (
        UniqueConstraint("user_id", "ingredient_name", name="uq_user_ingredient"),
    )
