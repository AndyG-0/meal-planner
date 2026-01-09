"""Authentication endpoints."""

import logging
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user
from app.database import get_db
from app.models import PasswordResetToken, User
from app.schemas import (
    PasswordResetConfirm,
    PasswordResetRequest,
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.utils.auth import (
    create_access_token_async,
    create_refresh_token,
    get_password_hash,
    verify_password,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/setup-required")
async def check_setup_required(db: AsyncSession = Depends(get_db)) -> dict[str, bool]:
    """Check if initial setup is required (no users exist)."""
    result = await db.execute(select(func.count(User.id)))
    user_count = result.scalar() or 0
    return {"setup_required": user_count == 0}


@router.post("/setup-admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def setup_initial_admin(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    """Create the first admin user. Only works when no users exist."""
    logger.info("Initial admin setup attempt")
    # Check if any users exist
    result = await db.execute(select(func.count(User.id)))
    user_count = result.scalar() or 0

    if user_count > 0:
        logger.warning("Initial setup already completed, rejecting setup-admin request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Initial setup has already been completed. Use the register endpoint instead.",
        )

    # Check if username would conflict (extra safety)
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        logger.warning("Setup-admin failed: Username already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email would conflict (extra safety)
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        logger.warning("Setup-admin failed: Email already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create first admin user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        is_admin=True,  # First user is automatically an admin
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("Initial admin user created successfully: user_id=%s", user.id)
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    """Register a new user."""
    logger.info("User registration attempt")
    # Check if username exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        logger.warning("Registration failed: Username already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        logger.warning("Registration failed: Email already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("User registered successfully: user_id=%s", user.id)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Login user and return access token."""
    logger.info("Login attempt")
    # Find user by username
    result = await db.execute(
        select(User).where(User.username == form_data.username, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning("Failed login attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with configurable TTL
    access_token = await create_access_token_async(data={"sub": str(user.id)}, db=db)
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    logger.info("Successful login for user_id=%s", user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current user information."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update current user information."""
    logger.info("User profile update for user_id=%s", current_user.id)
    # Update allowed fields
    update_data = user_update.model_dump(exclude_unset=True)

    # Handle password update separately
    if "password" in update_data:
        logger.info("Password change for user_id=%s", current_user.id)
        current_user.password_hash = get_password_hash(update_data["password"])
        del update_data["password"]

    # Check if email is being changed and if it's already taken
    if "email" in update_data:
        logger.debug("Email change requested for user_id=%s", current_user.id)
        result = await db.execute(
            select(User).where(
                User.email == update_data["email"],
                User.id != current_user.id,
                User.deleted_at.is_(None),
            )
        )
        if result.scalar_one_or_none():
            logger.warning("Email change failed for user_id=%s: Email already registered", current_user.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # Update other fields
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    logger.info("User profile updated successfully for user_id=%s", current_user.id)
    return current_user


@router.get("/users/search", response_model=list[UserResponse])
async def search_users(
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    limit: int = 10,
) -> list[User]:
    """Search for users by username or email."""
    if not q or len(q) < 2:
        return []

    logger.debug("User search: requested_by=%s", current_user.id)
    search_pattern = f"%{q}%"
    result = await db.execute(
        select(User)
        .where(
            User.deleted_at.is_(None),
            (User.username.ilike(search_pattern) | User.email.ilike(search_pattern)),
        )
        .limit(limit)
    )
    users = result.scalars().all()
    logger.debug("User search returned %d results", len(users))
    return users


@router.post("/forgot-password")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Request a password reset token."""
    logger.info("Password reset requested")
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == reset_request.email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    # Always return success even if user not found (security best practice)
    if not user:
        logger.debug("Password reset requested for non-existent email")
        return {"message": "If the email exists in our system, a password reset link will be sent."}

    # Invalidate any existing tokens for this user
    await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)
        )
    )
    existing_tokens = (
        (
            await db.execute(
                select(PasswordResetToken).where(
                    PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)
                )
            )
        )
        .scalars()
        .all()
    )

    for token in existing_tokens:
        token.used_at = datetime.utcnow()

    # Generate secure token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    # Create token record
    token_record = PasswordResetToken(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at,
    )
    db.add(token_record)
    await db.commit()

    logger.info("Password reset token generated for user_id=%s", user.id)
    # TODO: Send email with reset link
    # For now, return the token (in production, this should be sent via email)
    # return {"message": "Password reset email sent"}

    # Development mode: return token directly
    return {
        "message": "Password reset token generated (in production, this would be emailed)",
        "token": reset_token,  # Remove in production
        "expires_in": "1 hour",
    }


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Reset password using a valid token."""
    logger.info("Password reset attempt with token")
    # Find token
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == reset_data.token,
            PasswordResetToken.used_at.is_(None),
        )
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        logger.warning("Invalid or already used password reset token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used reset token",
        )

    # Check if token is expired
    if token_record.expires_at < datetime.utcnow():
        logger.warning("Expired password reset token for user_id=%s", token_record.user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    # Get user
    user_result = await db.execute(
        select(User).where(User.id == token_record.user_id, User.deleted_at.is_(None))
    )
    user = user_result.scalar_one_or_none()

    if not user:
        logger.error("User not found for password reset token: user_id=%s", token_record.user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update password
    user.password_hash = get_password_hash(reset_data.new_password)

    # Mark token as used
    token_record.used_at = datetime.utcnow()

    await db.commit()

    logger.info("Password reset successful for user_id=%s", user.id)
    return {"message": "Password has been reset successfully"}
