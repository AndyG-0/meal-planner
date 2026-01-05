"""Authentication utilities."""

from datetime import datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """Hash a password."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


async def get_session_ttl_timedelta(db: AsyncSession | None = None) -> timedelta:
    """Get the configured session TTL as a timedelta."""
    if db is None:
        # Fallback to default if no database session provided
        return timedelta(days=90)

    try:
        from app.models import SessionSettings

        result = await db.execute(select(SessionSettings).where(SessionSettings.id == 1))
        session_settings = result.scalar_one_or_none()

        if not session_settings:
            # Return default if not configured
            return timedelta(days=90)

        # Convert the configured value to timedelta
        if session_settings.session_ttl_unit == "minutes":
            return timedelta(minutes=session_settings.session_ttl_value)
        elif session_settings.session_ttl_unit == "hours":
            return timedelta(hours=session_settings.session_ttl_value)
        else:  # days
            return timedelta(days=session_settings.session_ttl_value)
    except Exception:
        # Fallback to default on any error
        return timedelta(days=90)


async def create_access_token_async(
    data: dict[str, Any], db: AsyncSession, expires_delta: timedelta | None = None
) -> str:
    """Create a JWT access token with configurable TTL (async version)."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Get the configured session TTL
        ttl = await get_session_ttl_timedelta(db)
        expire = datetime.utcnow() + ttl
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token (sync version - uses default TTL)."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
