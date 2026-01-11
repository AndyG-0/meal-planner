"""Schemas for blocked image domains."""

from datetime import datetime

from pydantic import BaseModel, Field


class BlockedDomainBase(BaseModel):
    """Base schema for blocked domain."""

    domain: str = Field(..., description="Domain to block (e.g., example.com)")
    reason: str | None = Field(None, description="Reason for blocking")


class BlockedDomainCreate(BlockedDomainBase):
    """Schema for creating a blocked domain."""

    pass


class BlockedDomainResponse(BlockedDomainBase):
    """Schema for blocked domain response."""

    id: int
    created_at: datetime
    created_by_id: int | None

    class Config:
        """Pydantic config."""

        from_attributes = True
