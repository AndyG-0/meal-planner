"""Feature toggles endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_db
from app.models import FeatureToggle

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/features", tags=["features"])


@router.get("/enabled")
async def get_enabled_features(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, bool]:
    """Get all enabled feature toggles (public endpoint)."""
    logger.debug("Fetching all enabled features")
    result = await db.execute(select(FeatureToggle).where(FeatureToggle.is_enabled))
    toggles = result.scalars().all()

    return {toggle.feature_key: True for toggle in toggles}


@router.get("/{feature_key}")
async def check_feature(
    feature_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, bool]:
    """Check if a specific feature is enabled (public endpoint)."""
    logger.debug("Checking feature: %s", feature_key)
    result = await db.execute(select(FeatureToggle).where(FeatureToggle.feature_key == feature_key))
    toggle = result.scalar_one_or_none()

    return {"enabled": toggle.is_enabled if toggle else False}
