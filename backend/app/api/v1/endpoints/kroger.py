"""Kroger API endpoints for location search, product search, and cart management."""

import logging
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, get_db
from app.models import (
    FeatureToggle,
    KrogerAppCart,
    KrogerBrandUrls,
    KrogerSettings,
    KrogerUserAuth,
    KrogerUserLocation,
    User,
)
from app.schemas import (
    KrogerAddToCartRequest,
    KrogerAddToCartResponse,
    KrogerAppCartItemCreate,
    KrogerAppCartItemResponse,
    KrogerAppCartItemUpdate,
    KrogerAppCartResponse,
    KrogerAuthCallbackRequest,
    KrogerAuthResponse,
    KrogerBrandUrlsCreate,
    KrogerBrandUrlsResponse,
    KrogerBrandUrlsUpdate,
    KrogerLocationCreate,
    KrogerLocationResponse,
    KrogerLocationSearchRequest,
    KrogerLocationSearchResponse,
    KrogerProductResponse,
    KrogerProductSearchRequest,
    KrogerProductSearchResponse,
    KrogerSendToKrogerRequest,
    KrogerSendToKrogerResponse,
    KrogerStoreLocationResponse,
)
from app.services.kroger_service import KrogerAPIError, get_kroger_service, get_user_location

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kroger", tags=["kroger"])


async def check_feature_enabled(db: AsyncSession, feature_key: str) -> None:
    """Check if a Kroger feature is enabled.

    Args:
        db: Database session.
        feature_key: Feature toggle key.

    Raises:
        HTTPException: If feature is not enabled.
    """
    result = await db.execute(select(FeatureToggle).where(FeatureToggle.feature_key == feature_key))
    toggle = result.scalar_one_or_none()

    if not toggle or not bool(toggle.is_enabled):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Kroger {feature_key.replace('kroger_', '').replace('_', ' ')} feature is not enabled",
        )


# Location Search Endpoints (requires kroger_product_search feature)


@router.post("/locations/search", response_model=KrogerLocationSearchResponse)
async def search_locations(
    request: KrogerLocationSearchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
) -> KrogerLocationSearchResponse:
    """Search for Kroger store locations."""
    await check_feature_enabled(db, "kroger_product_search")

    service = await get_kroger_service(db)
    if not service.has_client_credentials():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kroger client credentials not configured",
        )

    try:
        response = await service.search_locations(
            zip_code=request.zip_code,
            lat_long=request.lat_long,
            radius_in_miles=request.radius_in_miles,
            limit=request.limit,
            chain=request.chain,
        )

        locations = []
        for loc_data in response.get("data", []):
            location = KrogerStoreLocationResponse(
                location_id=loc_data.get("locationId", ""),
                name=loc_data.get("name", ""),
                address=loc_data.get("address", {}).get("addressLine1"),
                city=loc_data.get("address", {}).get("city"),
                state=loc_data.get("address", {}).get("state"),
                zip_code=loc_data.get("address", {}).get("zipCode"),
                phone=loc_data.get("phone"),
                chain=loc_data.get("chain"),
                distance=loc_data.get("distance"),
                hours=loc_data.get("hours"),
                departments=[dept.get("name", "") for dept in loc_data.get("departments", [])],
            )
            locations.append(location)

        return KrogerLocationSearchResponse(
            locations=locations,
            total=response.get("meta", {}).get("total", len(locations)),
        )

    except KrogerAPIError as e:
        logger.error("Kroger location search failed: %s", e)

        # Map Kroger API errors to appropriate HTTP status codes
        if hasattr(e, 'status_code') and e.status_code:
            if 400 <= e.status_code < 500:
                if e.status_code == 403:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied to Kroger API. Please check your API credentials. {str(e)}",
                    ) from e
                else:
                    raise HTTPException(
                        status_code=e.status_code,
                        detail=f"Kroger API error: {str(e)}",
                    ) from e
            elif e.status_code >= 500:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Kroger service temporarily unavailable: {str(e)}",
                ) from e

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Kroger location search failed: {str(e)}",
        ) from e


@router.post("/locations/save", response_model=KrogerLocationResponse)
async def save_user_location(
    location_data: KrogerLocationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KrogerLocationResponse:
    """Save user's preferred Kroger location."""
    await check_feature_enabled(db, "kroger_product_search")

    # Check if user already has a location
    result = await db.execute(
        select(KrogerUserLocation).where(KrogerUserLocation.user_id == current_user.id)
    )
    user_location = result.scalar_one_or_none()

    if user_location:
        # Update existing location - use SQLAlchemy update
        from sqlalchemy import update as sa_update

        stmt = (
            sa_update(KrogerUserLocation)
            .where(KrogerUserLocation.user_id == current_user.id)
            .values(
                location_id=location_data.location_id,
                location_name=location_data.location_name,
                location_address=location_data.location_address,
                location_chain=location_data.location_chain,
                location_data=location_data.location_data,
            )
        )
        await db.execute(stmt)
        await db.commit()
        await db.refresh(user_location)
    else:
        # Create new location
        user_location = KrogerUserLocation(
            user_id=current_user.id,
            location_id=location_data.location_id,
            location_name=location_data.location_name,
            location_address=location_data.location_address,
            location_chain=location_data.location_chain,
            location_data=location_data.location_data,
        )
        db.add(user_location)

    await db.commit()
    await db.refresh(user_location)

    return KrogerLocationResponse.model_validate(user_location)


@router.get("/locations/current", response_model=KrogerLocationResponse | None)
async def get_current_location(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KrogerLocationResponse | None:
    """Get user's currently saved Kroger location."""
    await check_feature_enabled(db, "kroger_product_search")

    user_location = await get_user_location(db, getattr(current_user, "id"))
    if user_location:
        return KrogerLocationResponse.model_validate(user_location)
    return None


# Product Search Endpoints (requires kroger_product_search feature)


@router.post("/products/search", response_model=KrogerProductSearchResponse)
async def search_products(
    request: KrogerProductSearchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
) -> KrogerProductSearchResponse:
    """Search for products in Kroger catalog."""
    await check_feature_enabled(db, "kroger_product_search")

    service = await get_kroger_service(db)
    if not service.has_client_credentials():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kroger client credentials not configured",
        )

    try:
        response = await service.search_products(
            term=request.term,
            location_id=request.location_id,
            fulfillment=request.fulfillment,
            limit=request.limit,
        )

        products = []
        for prod_data in response.get("data", []):
            # Extract price information from items array
            items = prod_data.get("items", [])
            first_item = items[0] if items else {}
            price_data = first_item.get("price", {})
            regular_price = price_data.get("regular")
            promo_price = price_data.get("promo")

            # Get product images
            images = prod_data.get("images", [])
            image_url = None
            if images:
                # Use the first perspective or featured image
                for img in images:
                    if img.get("perspective") in ["front", "featured"]:
                        # Get first size URL
                        sizes = img.get("sizes", [])
                        if sizes:
                            image_url = sizes[0].get("url")
                        break
                # Fallback to first image's first size
                if not image_url and images:
                    sizes = images[0].get("sizes", [])
                    if sizes:
                        image_url = sizes[0].get("url")

            # Get aisle locations (directly on product, not in items)
            aisle_locations = prod_data.get("aisleLocations", [])

            product = KrogerProductResponse(
                product_id=prod_data.get("productId", ""),
                upc=first_item.get("itemId"),  # UPC is itemId in Product API
                brand=prod_data.get("brand"),
                description=prod_data.get("description", ""),
                size=first_item.get("size"),
                price=promo_price if promo_price else regular_price,
                regular_price=regular_price,
                on_sale=bool(promo_price and regular_price and promo_price < regular_price),
                image_url=image_url,
                categories=prod_data.get("categories", []),
                aisle_locations=aisle_locations,
            )
            products.append(product)

        # Product API doesn't return pagination metadata like Catalog API
        # Just return what we have
        return KrogerProductSearchResponse(
            products=products,
            total=len(products),
            has_more=len(products) >= request.limit,  # If we got a full page, there might be more
        )

    except KrogerAPIError as e:
        logger.error("Kroger product search failed: %s", e)

        # Map Kroger API errors to appropriate HTTP status codes
        if hasattr(e, 'status_code') and e.status_code:
            # Client errors (4xx) - pass through
            if 400 <= e.status_code < 500:
                if e.status_code == 403:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied to Kroger API. Please check your API credentials and permissions. {str(e)}",
                    ) from e
                elif e.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Kroger resource not found: {str(e)}",
                    ) from e
                else:
                    raise HTTPException(
                        status_code=e.status_code,
                        detail=f"Kroger API error: {str(e)}",
                    ) from e
            # Server errors (5xx)
            elif e.status_code >= 500:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Kroger service temporarily unavailable: {str(e)}",
                ) from e

        # Default to 503 for unknown errors
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Kroger product search failed: {str(e)}",
        ) from e


# OAuth2 and Cart Endpoints (requires kroger_shopping_cart feature)


@router.get("/auth/authorize")
async def get_auth_url(
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Get Kroger OAuth2 authorization URL."""
    await check_feature_enabled(db, "kroger_shopping_cart")

    service = await get_kroger_service(db)
    if not service.has_oauth_credentials():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kroger OAuth credentials not configured",
        )

    # Generate a state token for CSRF protection
    state = secrets.token_urlsafe(32)

    auth_url = service.get_authorization_url(state=state)

    return {"authorization_url": auth_url, "state": state}


@router.post("/auth/callback", response_model=KrogerAuthResponse)
async def handle_auth_callback(
    callback_data: KrogerAuthCallbackRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KrogerAuthResponse:
    """Handle OAuth2 callback and exchange code for tokens."""
    await check_feature_enabled(db, "kroger_shopping_cart")

    service = await get_kroger_service(db)

    try:
        from datetime import datetime, timedelta

        # Exchange code for tokens
        token_data = await service.exchange_code_for_token(callback_data.code)

        # Store tokens in database
        result = await db.execute(
            select(KrogerUserAuth).where(KrogerUserAuth.user_id == current_user.id)
        )
        user_auth = result.scalar_one_or_none()

        expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))

        if user_auth:
            # Update existing auth - use SQLAlchemy update
            from sqlalchemy import update as sa_update

            stmt = (
                sa_update(KrogerUserAuth)
                .where(KrogerUserAuth.user_id == getattr(current_user, "id"))
                .values(
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token"),
                    expires_at=expires_at,
                    scope=token_data.get("scope"),
                )
            )
            await db.execute(stmt)
            await db.commit()
            await db.refresh(user_auth)
        else:
            # Create new auth
            user_auth = KrogerUserAuth(
                user_id=current_user.id,
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                expires_at=expires_at,
                scope=token_data.get("scope"),
            )
            db.add(user_auth)

        await db.commit()
        await db.refresh(user_auth)

        return KrogerAuthResponse(
            authenticated=True,
            expires_at=expires_at,
        )

    except KrogerAPIError as e:
        logger.error("Kroger auth callback failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}",
        ) from e


@router.get("/auth/status", response_model=KrogerAuthResponse)
async def get_auth_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KrogerAuthResponse:
    """Get current Kroger authentication status."""
    await check_feature_enabled(db, "kroger_shopping_cart")

    result = await db.execute(select(KrogerUserAuth).where(KrogerUserAuth.user_id == current_user.id))
    user_auth = result.scalar_one_or_none()

    if not user_auth:
        return KrogerAuthResponse(authenticated=False)

    from datetime import datetime

    # Check if token is expired
    is_valid = datetime.utcnow() < user_auth.expires_at  # type: ignore[operator]

    return KrogerAuthResponse(
        authenticated=bool(is_valid),
        kroger_user_id=getattr(user_auth, "kroger_user_id", None),
        kroger_email=getattr(user_auth, "kroger_email", None),
        kroger_name=getattr(user_auth, "kroger_name", None),
        expires_at=user_auth.expires_at,  # type: ignore[arg-type]
    )


@router.post("/cart/add", response_model=KrogerAddToCartResponse)
async def add_to_cart(
    request: KrogerAddToCartRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KrogerAddToCartResponse:
    """Add items to Kroger cart."""
    await check_feature_enabled(db, "kroger_shopping_cart")

    service = await get_kroger_service(db)

    try:
        # Convert items to format expected by service
        items = [
            {
                "upc": item.upc,
                "quantity": item.quantity,
                "modality": item.modality if item.modality else None,
            }
            for item in request.items
        ]

        logger.info("Add to cart request payload: %s", {"items": items})

        result = await service.add_to_cart(db, getattr(current_user, "id"), items)

        return KrogerAddToCartResponse(
            success=result.get("success", False),
            message="Items added to cart successfully" if result.get("success") else "Failed to add items",
            items_added=result.get("items_added", 0),
        )

    except KrogerAPIError as e:
        logger.error("Add to cart failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to add items to cart: {str(e)}",
        ) from e


@router.get("/checkout-url", response_model=dict)
async def get_checkout_url(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Get the checkout URL for the current environment and user's selected brand."""
    await check_feature_enabled(db, "kroger_shopping_cart")

    # Get user's location to determine the brand
    result = await db.execute(
        select(KrogerUserLocation).where(KrogerUserLocation.user_id == current_user.id)
    )
    user_location = result.scalar_one_or_none()

    # Get settings to determine environment
    result = await db.execute(select(KrogerSettings).where(KrogerSettings.id == 1))
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kroger settings not found",
        )

    environment = getattr(settings, "environment", "production")

    # Try to get brand-specific URL if user has a location
    checkout_url = None
    brand_used = None

    if user_location and user_location.location_chain:
        # Normalize the chain name to uppercase for matching
        chain_normalized = user_location.location_chain.upper()

        # Query for brand-specific URLs
        result = await db.execute(
            select(KrogerBrandUrls).where(
                KrogerBrandUrls.brand == chain_normalized,
                KrogerBrandUrls.is_active == True  # noqa: E712
            )
        )
        brand_urls = result.scalar_one_or_none()

        if brand_urls:
            checkout_url = (
                brand_urls.certification_checkout_url
                if environment == "certification"
                else brand_urls.checkout_url
            )
            brand_used = brand_urls.brand

    # Fallback to settings default URLs if no brand-specific URL found
    if not checkout_url:
        checkout_url = (
            getattr(settings, "certification_checkout_url", None)
            if environment == "certification"
            else getattr(settings, "checkout_url", None)
        )

    if not checkout_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkout URL not configured for {environment} environment"
            + (f" and brand {brand_used}" if brand_used else ""),
        )

    return {
        "checkout_url": checkout_url,
        "environment": environment,
        "brand": brand_used,
    }

@router.get("/cart-url", response_model=dict)
async def get_cart_url(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Get the cart view URL for the current environment and user's selected brand."""
    await check_feature_enabled(db, "kroger_shopping_cart")

    # Get user's location to determine the brand
    result = await db.execute(
        select(KrogerUserLocation).where(KrogerUserLocation.user_id == current_user.id)
    )
    user_location = result.scalar_one_or_none()

    # Get settings to determine environment
    result = await db.execute(select(KrogerSettings).where(KrogerSettings.id == 1))
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kroger settings not found",
        )

    environment = getattr(settings, "environment", "production")

    # Try to get brand-specific URL if user has a location
    cart_url = None
    brand_used = None

    if user_location and user_location.location_chain:
        # Normalize the chain name to uppercase for matching
        chain_normalized = user_location.location_chain.upper()

        # Query for brand-specific URLs
        result = await db.execute(
            select(KrogerBrandUrls).where(
                KrogerBrandUrls.brand == chain_normalized,
                KrogerBrandUrls.is_active == True  # noqa: E712
            )
        )
        brand_urls = result.scalar_one_or_none()

        if brand_urls:
            cart_url = (
                brand_urls.certification_cart_url
                if environment == "certification"
                else brand_urls.cart_url
            )
            brand_used = brand_urls.brand

    # Fallback to settings default URLs if no brand-specific URL found
    if not cart_url:
        cart_url = (
            getattr(settings, "certification_cart_url", None)
            if environment == "certification"
            else getattr(settings, "cart_url", None)
        )

    if not cart_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cart URL not configured for {environment} environment"
            + (f" and brand {brand_used}" if brand_used else ""),
        )

    return {
        "cart_url": cart_url,
        "environment": environment,
        "brand": brand_used,
    }

@router.get("/cart", response_model=dict)
async def get_cart(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Get user's current Kroger cart."""
    await check_feature_enabled(db, "kroger_shopping_cart")

    service = await get_kroger_service(db)

    try:
        result = await service.get_cart(db, getattr(current_user, "id"))

        # Import the schema
        from app.schemas import KrogerCartResponse
        return KrogerCartResponse(**result).model_dump(exclude_none=True)

    except KrogerAPIError as e:
        logger.error("Get cart failed: %s", e)

        # Check for specific error types
        if "401" in str(e) or "unauthorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kroger authorization expired. Please reconnect your account.",
            ) from e

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to retrieve cart: {str(e)}",
        ) from e


@router.post("/logout")
async def logout(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Logout user from Kroger and delete stored OAuth tokens."""
    try:
        # Delete the user's Kroger OAuth token from database
        user_id = getattr(current_user, "id")
        result = await db.execute(
            select(KrogerUserAuth).where(KrogerUserAuth.user_id == user_id)
        )
        kroger_auth = result.scalars().first()

        if kroger_auth:
            await db.delete(kroger_auth)
            await db.commit()
            logger.info("User %s logged out from Kroger", user_id)
            return {"message": "Successfully logged out from Kroger"}

        return {"message": "No active Kroger session to logout"}

    except Exception as e:
        logger.error("Logout failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout from Kroger",
        ) from e


# Admin endpoints for managing brand URLs


@router.get("/admin/brands", response_model=list[KrogerBrandUrlsResponse])
async def list_brand_urls(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[KrogerBrandUrlsResponse]:
    """List all Kroger brand URLs (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    result = await db.execute(select(KrogerBrandUrls).order_by(KrogerBrandUrls.brand))
    brands = result.scalars().all()
    return [KrogerBrandUrlsResponse.model_validate(brand) for brand in brands]


@router.post("/admin/brands", response_model=KrogerBrandUrlsResponse, status_code=status.HTTP_201_CREATED)
async def create_brand_url(
    brand_data: KrogerBrandUrlsCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KrogerBrandUrlsResponse:
    """Create a new Kroger brand URL configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Check if brand already exists
    result = await db.execute(
        select(KrogerBrandUrls).where(KrogerBrandUrls.brand == brand_data.brand.upper())
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Brand {brand_data.brand} already exists",
        )

    # Create new brand URL entry
    brand_urls = KrogerBrandUrls(
        brand=brand_data.brand.upper(),
        display_name=brand_data.display_name,
        cart_url=brand_data.cart_url,
        checkout_url=brand_data.checkout_url,
        certification_cart_url=brand_data.certification_cart_url,
        certification_checkout_url=brand_data.certification_checkout_url,
        is_active=brand_data.is_active,
    )

    db.add(brand_urls)
    await db.commit()
    await db.refresh(brand_urls)

    return KrogerBrandUrlsResponse.model_validate(brand_urls)


@router.put("/admin/brands/{brand_id}", response_model=KrogerBrandUrlsResponse)
async def update_brand_url(
    brand_id: int,
    brand_data: KrogerBrandUrlsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KrogerBrandUrlsResponse:
    """Update a Kroger brand URL configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Get existing brand
    result = await db.execute(select(KrogerBrandUrls).where(KrogerBrandUrls.id == brand_id))
    brand_urls = result.scalar_one_or_none()

    if not brand_urls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found",
        )

    # Update fields
    update_data = brand_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(brand_urls, field, value)

    await db.commit()
    await db.refresh(brand_urls)

    return KrogerBrandUrlsResponse.model_validate(brand_urls)


@router.delete("/admin/brands/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand_url(
    brand_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a Kroger brand URL configuration (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Get existing brand
    result = await db.execute(select(KrogerBrandUrls).where(KrogerBrandUrls.id == brand_id))
    brand_urls = result.scalar_one_or_none()

    if not brand_urls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found",
        )

    await db.delete(brand_urls)
    await db.commit()


# In-App Kroger Cart Endpoints


@router.get("/app-cart", response_model=KrogerAppCartResponse)
async def get_app_cart(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KrogerAppCartResponse:
    """Get the user's in-app Kroger cart."""
    await check_feature_enabled(db, "kroger_product_search")

    result = await db.execute(
        select(KrogerAppCart)
        .where(KrogerAppCart.user_id == current_user.id)
        .order_by(KrogerAppCart.created_at.desc())
    )
    cart_items = result.scalars().all()

    # Group by fulfillment type - the cart should only have one type
    fulfillment_type = "PICKUP"
    if cart_items:
        fulfillment_type = cart_items[0].fulfillment_type

    total_quantity = sum(item.quantity for item in cart_items)
    estimated_total = sum((item.price or 0) * item.quantity for item in cart_items)

    return KrogerAppCartResponse(
        items=[KrogerAppCartItemResponse.model_validate(item) for item in cart_items],
        total_items=len(cart_items),
        total_quantity=total_quantity,
        estimated_total=estimated_total if estimated_total > 0 else None,
        fulfillment_type=fulfillment_type,
    )


@router.post("/app-cart/items", response_model=KrogerAppCartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_app_cart(
    item_data: KrogerAppCartItemCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KrogerAppCartItemResponse:
    """Add an item to the in-app Kroger cart."""
    await check_feature_enabled(db, "kroger_product_search")

    # Check if user is switching fulfillment types
    result = await db.execute(
        select(KrogerAppCart)
        .where(KrogerAppCart.user_id == current_user.id)
        .limit(1)
    )
    existing_item = result.scalar_one_or_none()

    if existing_item and existing_item.fulfillment_type != item_data.fulfillment_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cart contains items for {existing_item.fulfillment_type}. Clear cart before switching to {item_data.fulfillment_type}.",
        )

    # Check if item already exists in cart
    result = await db.execute(
        select(KrogerAppCart)
        .where(KrogerAppCart.user_id == current_user.id)
        .where(KrogerAppCart.product_id == item_data.product_id)
    )
    existing_cart_item = result.scalar_one_or_none()

    if existing_cart_item:
        # Update quantity
        existing_cart_item.quantity += item_data.quantity
        await db.commit()
        await db.refresh(existing_cart_item)
        return KrogerAppCartItemResponse.model_validate(existing_cart_item)

    # Create new cart item
    cart_item = KrogerAppCart(
        user_id=current_user.id,
        product_id=item_data.product_id,
        upc=item_data.upc,
        product_name=item_data.product_name,
        brand=item_data.brand,
        size=item_data.size,
        price=item_data.price,
        image_url=item_data.image_url,
        quantity=item_data.quantity,
        fulfillment_type=item_data.fulfillment_type,
        grocery_list_item_name=item_data.grocery_list_item_name,
    )

    db.add(cart_item)
    await db.commit()
    await db.refresh(cart_item)

    return KrogerAppCartItemResponse.model_validate(cart_item)


@router.patch("/app-cart/items/{item_id}", response_model=KrogerAppCartItemResponse)
async def update_cart_item(
    item_id: int,
    item_data: KrogerAppCartItemUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KrogerAppCartItemResponse:
    """Update a cart item's quantity or fulfillment type."""
    await check_feature_enabled(db, "kroger_product_search")

    result = await db.execute(
        select(KrogerAppCart)
        .where(KrogerAppCart.id == item_id)
        .where(KrogerAppCart.user_id == current_user.id)
    )
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    # If changing fulfillment type, ensure no other items exist
    if item_data.fulfillment_type and item_data.fulfillment_type != cart_item.fulfillment_type:
        result = await db.execute(
            select(KrogerAppCart)
            .where(KrogerAppCart.user_id == current_user.id)
            .where(KrogerAppCart.id != item_id)
        )
        other_items = result.scalars().all()
        if other_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change fulfillment type when other items exist in cart. Clear cart first.",
            )

    # Update fields
    update_data = item_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cart_item, field, value)

    await db.commit()
    await db.refresh(cart_item)

    return KrogerAppCartItemResponse.model_validate(cart_item)


@router.delete("/app-cart/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_app_cart(
    item_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Remove an item from the in-app cart."""
    await check_feature_enabled(db, "kroger_product_search")

    result = await db.execute(
        select(KrogerAppCart)
        .where(KrogerAppCart.id == item_id)
        .where(KrogerAppCart.user_id == current_user.id)
    )
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    await db.delete(cart_item)
    await db.commit()


@router.delete("/app-cart", status_code=status.HTTP_204_NO_CONTENT)
async def clear_app_cart(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Clear all items from the in-app cart."""
    await check_feature_enabled(db, "kroger_product_search")

    result = await db.execute(
        select(KrogerAppCart).where(KrogerAppCart.user_id == current_user.id)
    )
    cart_items = result.scalars().all()

    for item in cart_items:
        await db.delete(item)

    await db.commit()


@router.post("/app-cart/send-to-kroger", response_model=KrogerSendToKrogerResponse)
async def send_cart_to_kroger(
    request: KrogerSendToKrogerRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> KrogerSendToKrogerResponse:
    """Send in-app cart items to Kroger. Requires Kroger authentication."""
    await check_feature_enabled(db, "kroger_shopping_cart")

    if not request.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must confirm that you understand the cart will be managed in Kroger after sending.",
        )

    # Get cart items
    result = await db.execute(
        select(KrogerAppCart)
        .where(KrogerAppCart.user_id == current_user.id)
        .order_by(KrogerAppCart.created_at)
    )
    cart_items = result.scalars().all()

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

    # Get Kroger service
    service = await get_kroger_service(db)

    # Check if user is authenticated (will be checked in service method too)
    result = await db.execute(
        select(KrogerUserAuth).where(KrogerUserAuth.user_id == current_user.id)
    )
    auth = result.scalar_one_or_none()

    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kroger authentication required",
        )

    # Map fulfillment type to modality
    modality_map = {
        "PICKUP": "PICKUP",
        "DELIVERY": "DELIVERY",
    }

    errors = []
    items_sent = 0

    # Send items to Kroger in batches to respect rate limits
    # Kroger API allows up to 50 items per request
    batch_size = 50
    for i in range(0, len(cart_items), batch_size):
        batch = cart_items[i:i + batch_size]

        try:
            kroger_items = [
                {
                    "upc": item.upc,
                    "quantity": item.quantity,
                    "modality": modality_map.get(item.fulfillment_type, "PICKUP"),
                }
                for item in batch
            ]

            # Add to Kroger cart
            await service.add_to_cart(
                db=db,
                user_id=current_user.id,
                items=kroger_items,
            )

            items_sent += len(batch)

        except KrogerAPIError as e:
            logger.error("Failed to send batch to Kroger: %s", e)
            errors.append(f"Batch {i // batch_size + 1}: {str(e)}")

    # Don't clear the cart here - let user do it manually after confirming items are in Kroger
    success = items_sent > 0

    return KrogerSendToKrogerResponse(
        success=success,
        message=f"Sent {items_sent} of {len(cart_items)} items to Kroger" if success else "Failed to send items to Kroger",
        items_sent=items_sent,
        errors=errors,
    )

