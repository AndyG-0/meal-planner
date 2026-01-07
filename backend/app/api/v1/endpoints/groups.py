"""Groups API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, get_db
from app.models import Group, GroupMember, User
from app.schemas import (
    GroupCreate,
    GroupMemberCreate,
    GroupMemberResponse,
    GroupResponse,
    GroupUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get("", response_model=list[GroupResponse])
async def get_user_groups(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[Group]:
    """Get groups where user is owner or member with pagination."""

    # Get groups owned by user
    owned_result = await db.execute(select(Group).where(Group.owner_id == current_user.id))
    owned_groups = owned_result.scalars().all()

    # Get groups where user is a member
    member_result = await db.execute(
        select(Group).join(GroupMember).where(GroupMember.user_id == current_user.id)
    )
    member_groups = member_result.scalars().all()

    # Combine and deduplicate
    all_groups = {group.id: group for group in owned_groups}
    for group in member_groups:
        if group.id not in all_groups:
            all_groups[group.id] = group

    # Apply pagination to combined results
    groups_list = list(all_groups.values())
    return groups_list[skip : skip + limit]


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Group:
    """Create a new group."""
    logger.info("Creating group: user_id=%s", current_user.id)
    group = Group(
        name=group_data.name,
        owner_id=current_user.id,
    )

    db.add(group)
    await db.commit()
    await db.refresh(group)

    logger.info("Group created successfully: group_id=%s", group.id)
    return group


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Group:
    """Get a specific group."""

    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    # Check if user has access (owner or member)
    if group.owner_id != current_user.id:
        member_result = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id, GroupMember.user_id == current_user.id
            )
        )
        if not member_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this group"
            )

    return group


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Group:
    """Update a group (owner only)."""

    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    if group.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner can update the group",
        )

    if group_data.name is not None:
        group.name = group_data.name

    await db.commit()
    await db.refresh(group)

    return group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a group (owner only)."""

    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    if group.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner can delete the group",
        )

    await db.delete(group)
    await db.commit()


@router.get("/{group_id}/members", response_model=list[GroupMemberResponse])
async def get_group_members(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[GroupMember]:
    """Get all members of a group with pagination."""

    # First check if group exists and user has access
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    # Check access
    if group.owner_id != current_user.id:
        member_result = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id, GroupMember.user_id == current_user.id
            )
        )
        if not member_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this group"
            )

    # Get all members
    result = await db.execute(
        select(GroupMember).where(GroupMember.group_id == group_id).offset(skip).limit(limit)
    )

    return result.scalars().all()


@router.post(
    "/{group_id}/members", response_model=GroupMemberResponse, status_code=status.HTTP_201_CREATED
)
async def add_group_member(
    group_id: int,
    member_data: GroupMemberCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> GroupMember:
    """Add a member to a group (owner or admin only)."""
    logger.info("Adding member to group: group_id=%s, new_user_id=%s, by_user_id=%s", 
                group_id, member_data.user_id, current_user.id)
    # Check if group exists
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()

    if not group:
        logger.warning("Group not found for member addition: group_id=%s", group_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    # Check permissions (must be owner or admin member)
    if group.owner_id != current_user.id:
        member_result = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == current_user.id,
                GroupMember.role == "admin",
            )
        )
        if not member_result.scalar_one_or_none():
            logger.warning("Unauthorized group member addition attempt: group_id=%s, user_id=%s", 
                          group_id, current_user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group owner or admin can add members",
            )

    # Check if user exists
    user_result = await db.execute(select(User).where(User.id == member_data.user_id))
    if not user_result.scalar_one_or_none():
        logger.warning("User not found for group member addition: user_id=%s", member_data.user_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if already a member
    existing_result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.user_id == member_data.user_id
        )
    )
    if existing_result.scalar_one_or_none():
        logger.debug("User already a member of group: group_id=%s, user_id=%s", group_id, member_data.user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this group"
        )

    # Add member
    member = GroupMember(
        group_id=group_id,
        user_id=member_data.user_id,
        role=member_data.role,
        permissions=member_data.permissions,
    )

    db.add(member)
    await db.commit()
    await db.refresh(member)

    return member


@router.delete("/{group_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group_member(
    group_id: int,
    member_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Remove a member from a group (owner, admin, or self only)."""

    # Get the group
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()

    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    # Get the member to remove
    member_result = await db.execute(
        select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.id == member_id)
    )
    member = member_result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    # Check permissions
    is_owner = group.owner_id == current_user.id
    is_self = member.user_id == current_user.id

    if not is_owner and not is_self:
        # Check if current user is admin
        admin_result = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == current_user.id,
                GroupMember.role == "admin",
            )
        )
        if not admin_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group owner, admin, or the member themselves can remove members",
            )

    await db.delete(member)
    await db.commit()
