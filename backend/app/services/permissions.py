"""Permissions service for handling access control."""

from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.models import Calendar, GroceryList, Recipe, User


class PermissionService:
    """Service for checking user permissions."""

    @staticmethod
    def can_view_recipe(db: Session, recipe: "Recipe", user: "User | None") -> bool:
        """Check if user can view a recipe."""
        # Public recipes are viewable by anyone
        if recipe.visibility == "public":
            return True

        # User must be authenticated for non-public recipes
        if not user:
            return False

        # Admins can view everything
        if user.is_admin:
            return True

        # Owner can always view
        if recipe.owner_id == user.id:
            return True

        # Group recipes can be viewed by group members
        if recipe.visibility == "group" and recipe.group_id:
            return PermissionService._is_group_member(db, recipe.group_id, user.id)

        return False

    @staticmethod
    def can_edit_recipe(db: Session, recipe: "Recipe", user: "User") -> bool:
        """Check if user can edit a recipe."""
        # Admins can edit everything
        if user.is_admin:
            return True

        # Owner can always edit
        if recipe.owner_id == user.id:
            return True

        # Group admins can edit group recipes
        if recipe.visibility == "group" and recipe.group_id:
            return PermissionService._is_group_admin(db, recipe.group_id, user.id)

        return False

    @staticmethod
    def can_delete_recipe(db: Session, recipe: "Recipe", user: "User") -> bool:
        """Check if user can delete a recipe."""
        # Admins can delete everything
        if user.is_admin:
            return True

        # Only owner can delete
        return recipe.owner_id == user.id

    @staticmethod
    def can_view_calendar(db: Session, calendar: "Calendar", user: "User | None") -> bool:
        """Check if user can view a calendar."""
        # Public calendars are viewable by anyone
        if calendar.visibility == "public":
            return True

        # User must be authenticated for non-public calendars
        if not user:
            return False

        # Admins can view everything
        if user.is_admin:
            return True

        # Owner can always view
        if calendar.owner_id == user.id:
            return True

        # Group calendars can be viewed by group members
        if calendar.visibility == "group" and calendar.group_id:
            return PermissionService._is_group_member(db, calendar.group_id, user.id)

        return False

    @staticmethod
    def can_edit_calendar(db: Session, calendar: "Calendar", user: "User") -> bool:
        """Check if user can edit a calendar."""
        # Admins can edit everything
        if user.is_admin:
            return True

        # Owner can always edit
        if calendar.owner_id == user.id:
            return True

        # Group admins can edit group calendars
        if calendar.visibility == "group" and calendar.group_id:
            return PermissionService._is_group_admin(db, calendar.group_id, user.id)

        return False

    @staticmethod
    def can_delete_calendar(db: Session, calendar: "Calendar", user: "User") -> bool:
        """Check if user can delete a calendar."""
        # Admins can delete everything
        if user.is_admin:
            return True

        # Only owner can delete
        return calendar.owner_id == user.id

    @staticmethod
    def can_view_grocery_list(
        db: Session, grocery_list: "GroceryList", user: "User | None"
    ) -> bool:
        """Check if user can view a grocery list."""
        # Public grocery lists are viewable by anyone
        if grocery_list.visibility == "public":
            return True

        # User must be authenticated for non-public grocery lists
        if not user:
            return False

        # Admins can view everything
        if user.is_admin:
            return True

        # Owner can always view
        if grocery_list.user_id == user.id:
            return True

        # Group grocery lists can be viewed by group members
        if grocery_list.visibility == "group" and grocery_list.group_id:
            return PermissionService._is_group_member(db, grocery_list.group_id, user.id)

        return False

    @staticmethod
    def can_edit_grocery_list(db: Session, grocery_list: "GroceryList", user: "User") -> bool:
        """Check if user can edit a grocery list."""
        # Admins can edit everything
        if user.is_admin:
            return True

        # Owner can always edit
        if grocery_list.user_id == user.id:
            return True

        # Group members can edit group grocery lists
        if grocery_list.visibility == "group" and grocery_list.group_id:
            return PermissionService._is_group_member(db, grocery_list.group_id, user.id)

        return False

    @staticmethod
    def can_delete_grocery_list(db: Session, grocery_list: "GroceryList", user: "User") -> bool:
        """Check if user can delete a grocery list."""
        # Admins can delete everything
        if user.is_admin:
            return True

        # Only owner can delete
        return grocery_list.user_id == user.id

    @staticmethod
    def _is_group_member(db: Session, group_id: int, user_id: int) -> bool:
        """Check if user is a member of a group."""
        from app.models import GroupMember

        member = (
            db.query(GroupMember)
            .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
            .first()
        )

        return member is not None

    @staticmethod
    def _is_group_admin(db: Session, group_id: int, user_id: int) -> bool:
        """Check if user is an admin of a group."""
        from app.models import Group, GroupMember

        # Check if user is group owner
        group = db.query(Group).filter(Group.id == group_id).first()
        if group and group.owner_id == user_id:
            return True

        # Check if user is a group admin
        member = (
            db.query(GroupMember)
            .filter(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
                GroupMember.role == "admin",
            )
            .first()
        )

        return member is not None
