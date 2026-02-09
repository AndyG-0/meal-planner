"""Kroger API service for product search, location search, and shopping cart integration."""

import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import KrogerSettings, KrogerUserAuth, KrogerUserLocation

logger = logging.getLogger(__name__)


class KrogerAPIError(Exception):
    """Exception raised for Kroger API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        """Initialize KrogerAPIError.

        Args:
            message: Error message.
            status_code: HTTP status code from Kroger API (if applicable).
        """
        super().__init__(message)
        self.status_code = status_code


class KrogerService:
    """Service for interacting with Kroger APIs."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        oauth_client_id: str | None = None,
        oauth_client_secret: str | None = None,
        redirect_uri: str | None = None,
        base_url: str | None = None,
    ):
        """Initialize Kroger API client.

        Args:
            client_id: Client ID for catalog/location APIs (client credentials flow).
            client_secret: Client secret for catalog/location APIs.
            oauth_client_id: OAuth client ID for cart/identity APIs (auth code flow).
            oauth_client_secret: OAuth client secret for cart/identity APIs.
            redirect_uri: Redirect URI for OAuth2 authorization code flow.
            base_url: Kroger API base URL.
        """
        self.client_id = client_id or settings.KROGER_CLIENT_ID
        self.client_secret = client_secret or settings.KROGER_CLIENT_SECRET
        self.oauth_client_id = oauth_client_id or settings.KROGER_OAUTH_CLIENT_ID
        self.oauth_client_secret = oauth_client_secret or settings.KROGER_OAUTH_CLIENT_SECRET
        self.redirect_uri = redirect_uri or settings.KROGER_REDIRECT_URI
        self.base_url = base_url or settings.KROGER_BASE_URL
        self._client_token: str | None = None
        self._client_token_expires: datetime | None = None

    def has_client_credentials(self) -> bool:
        """Check if client credentials are configured."""
        return bool(self.client_id and self.client_secret)

    def has_oauth_credentials(self) -> bool:
        """Check if OAuth credentials are configured."""
        return bool(self.oauth_client_id and self.oauth_client_secret and self.redirect_uri)

    async def get_client_credentials_token(self) -> str:
        """Get access token using client credentials flow (for catalog/location APIs).

        Returns:
            Access token string.

        Raises:
            KrogerAPIError: If credentials are not configured or token request fails.
        """
        if not self.has_client_credentials():
            raise KrogerAPIError("Kroger client credentials not configured")

        # Check if we have a valid cached token
        if self._client_token and self._client_token_expires:
            if datetime.utcnow() < self._client_token_expires:
                return self._client_token

        # Request new token
        async with httpx.AsyncClient() as client:
            try:
                logger.debug("Requesting Kroger access token with scope: product.compact")
                response = await client.post(
                    f"{self.base_url}/v1/connect/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "scope": "product.compact",
                    },
                    auth=(self.client_id, self.client_secret),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
                data = response.json()

                self._client_token = data["access_token"]
                # Set expiration to 5 minutes before actual expiration for safety
                expires_in = data.get("expires_in", 3600)
                self._client_token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 300)

                if not self._client_token:
                    raise KrogerAPIError("Failed to get access token from response")

                logger.debug("Successfully obtained Kroger access token (expires in %ss)", expires_in)
                logger.debug("Token scopes granted by Kroger: %s", data.get("scope", "not provided"))
                logger.debug("Token (first 20 chars): %s...", self._client_token[:20])
                return self._client_token

            except httpx.HTTPStatusError as e:
                logger.error(
                    "Failed to get Kroger client credentials token: HTTP %s - %s",
                    e.response.status_code,
                    e.response.text,
                )
                raise KrogerAPIError(
                    f"Failed to get access token: HTTP {e.response.status_code}"
                ) from e
            except httpx.HTTPError as e:
                logger.error("Failed to get Kroger client credentials token: %s", e)
                raise KrogerAPIError(f"Failed to get access token: {e}") from e

    async def search_locations(
        self,
        zip_code: str | None = None,
        lat_long: str | None = None,
        radius_in_miles: int = 10,
        limit: int = 10,
        chain: str | None = None,
    ) -> dict[str, Any]:
        """Search for Kroger store locations.

        Args:
            zip_code: ZIP code to search near.
            lat_long: Latitude and longitude to search near (format: "lat,long").
            radius_in_miles: Search radius in miles (1-100).
            limit: Maximum number of results (1-200).
            chain: Optional chain filter (e.g., "kroger", "ralphs").

        Returns:
            Dictionary with location data.

        Raises:
            KrogerAPIError: If the search fails.
        """
        token = await self.get_client_credentials_token()

        params: dict[str, Any] = {
            "filter.radiusInMiles": radius_in_miles,
            "filter.limit": limit,
        }

        if zip_code:
            params["filter.zipCode.near"] = zip_code
        elif lat_long:
            params["filter.latLong.near"] = lat_long
        else:
            raise KrogerAPIError("Either zip_code or lat_long must be provided")

        if chain:
            params["filter.chain"] = chain

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/v1/locations",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(
                    "Kroger location search failed: HTTP %s - URL: %s - Response: %s",
                    e.response.status_code,
                    e.request.url,
                    e.response.text[:500],
                )
                raise KrogerAPIError(
                    f"Location search failed: HTTP {e.response.status_code} - {e.response.text[:200]}",
                    status_code=e.response.status_code,
                ) from e
            except httpx.HTTPError as e:
                logger.error("Failed to search Kroger locations: %s", e)
                raise KrogerAPIError(f"Location search failed: {e}") from e

    async def search_products(
        self,
        term: str,
        location_id: str,
        fulfillment: str = "PICKUP",
        limit: int = 20,
        start: int = 0,
    ) -> dict[str, Any]:
        """Search for products in the Kroger catalog.

        Args:
            term: Search term.
            location_id: 8-character location ID.
            fulfillment: Fulfillment type (PICKUP, DELIVERY).
            limit: Number of results per page (1-50).
            start: Starting offset for pagination.

        Returns:
            Dictionary with product data.

        Raises:
            KrogerAPIError: If the search fails.
        """
        token = await self.get_client_credentials_token()
        logger.debug("Using token (first 20 chars): %s... for location %s", token[:20], location_id)

        # Map fulfillment types to Product API format
        fulfillment_map = {
            "PICKUP": "csp",   # Curbside Pickup
            "DELIVERY": "dth", # Delivery To Home
        }
        api_fulfillment = fulfillment_map.get(fulfillment.upper(), "csp")

        params = {
            "filter.term": term,
            "filter.locationId": location_id,
            "filter.fulfillment": api_fulfillment,
            "filter.limit": limit,
            "filter.start": start,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/v1/products",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(
                    "Kroger product search failed: HTTP %s - URL: %s - Response: %s",
                    e.response.status_code,
                    e.request.url,
                    e.response.text[:500],
                )
                # Preserve the original HTTP status code
                raise KrogerAPIError(
                    f"Product search failed: HTTP {e.response.status_code} - {e.response.text[:200]}",
                    status_code=e.response.status_code,
                ) from e
            except httpx.HTTPError as e:
                logger.error("Failed to search Kroger products: %s", e)
                raise KrogerAPIError(f"Product search failed: {e}") from e

    async def get_product_details(
        self,
        product_id: str,
        location_id: str,
        fulfillment: str = "INSTORE",
    ) -> dict[str, Any]:
        """Get detailed information for a specific product.

        Args:
            product_id: Product ID or UPC.
            location_id: 8-character location ID.
            fulfillment: Fulfillment type (INSTORE, PICKUP, DELIVERY, SHIP).

        Returns:
            Dictionary with product details.

        Raises:
            KrogerAPIError: If the request fails.
        """
        token = await self.get_client_credentials_token()

        # Map fulfillment types to Product API format
        fulfillment_map = {
            "INSTORE": "ais",
            "PICKUP": "csp",
            "DELIVERY": "dth",
            "SHIP": "sth",
        }
        api_fulfillment = fulfillment_map.get(fulfillment.upper(), "ais")

        params = {
            "filter.locationId": location_id,
            "filter.fulfillment": api_fulfillment,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/v1/products/{product_id}",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPError as e:
                logger.error("Failed to get Kroger product details: %s", e)
                raise KrogerAPIError(f"Product details request failed: {e}") from e

    def get_authorization_url(self, state: str | None = None) -> str:
        """Get OAuth2 authorization URL for cart/identity/profile access.

        Args:
            state: Optional state parameter for CSRF protection.

        Returns:
            Authorization URL string.

        Raises:
            KrogerAPIError: If OAuth credentials are not configured.
        """
        if not self.has_oauth_credentials():
            raise KrogerAPIError("Kroger OAuth credentials not configured")

        params = {
            "client_id": self.oauth_client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "cart.basic:write",
        }

        if state:
            params["state"] = state

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.base_url}/v1/connect/oauth2/authorize?{query_string}"

    async def exchange_code_for_token(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth2 callback.

        Returns:
            Dictionary with token data.

        Raises:
            KrogerAPIError: If token exchange fails.
        """
        if not self.has_oauth_credentials():
            raise KrogerAPIError("Kroger OAuth credentials not configured")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/connect/oauth2/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": self.redirect_uri,
                    },
                    auth=(self.oauth_client_id, self.oauth_client_secret),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPError as e:
                logger.error("Failed to exchange Kroger authorization code: %s", e)
                raise KrogerAPIError(f"Token exchange failed: {e}") from e

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh an expired access token.

        Args:
            refresh_token: Refresh token.

        Returns:
            Dictionary with new token data.

        Raises:
            KrogerAPIError: If token refresh fails.
        """
        if not self.has_oauth_credentials():
            raise KrogerAPIError("Kroger OAuth credentials not configured")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/connect/oauth2/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                    },
                    auth=(self.oauth_client_id, self.oauth_client_secret),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPError as e:
                logger.error("Failed to refresh Kroger access token: %s", e)
                raise KrogerAPIError(f"Token refresh failed: {e}") from e

    async def get_user_access_token(
        self, db: AsyncSession, user_id: int, auto_refresh: bool = True
    ) -> str:
        """Get user's access token, refreshing if necessary.

        Args:
            db: Database session.
            user_id: User ID.
            auto_refresh: Whether to automatically refresh expired tokens.

        Returns:
            Access token string.

        Raises:
            KrogerAPIError: If user is not authenticated or token refresh fails.
        """
        result = await db.execute(select(KrogerUserAuth).where(KrogerUserAuth.user_id == user_id))
        auth = result.scalar_one_or_none()

        if not auth:
            raise KrogerAPIError("User is not authenticated with Kroger")

        # Check if token is expired
        now = datetime.utcnow()
        if now >= auth.expires_at:  # type: ignore[operator]
            if not auto_refresh or not auth.refresh_token:  # type: ignore[truthy-function]
                raise KrogerAPIError("Access token expired and cannot be refreshed")

            # Refresh the token
            token_data = await self.refresh_access_token(str(auth.refresh_token))

            # Update database with new token data
            new_expires_at = now + timedelta(seconds=token_data.get("expires_in", 3600))

            # Update using SQLAlchemy update
            from sqlalchemy import update as sa_update
            stmt = (
                sa_update(KrogerUserAuth)
                .where(KrogerUserAuth.user_id == user_id)
                .values(
                    access_token=token_data["access_token"],
                    expires_at=new_expires_at,
                    refresh_token=token_data.get("refresh_token", auth.refresh_token),
                    updated_at=now,
                )
            )
            await db.execute(stmt)
            await db.commit()
            await db.refresh(auth)

        return str(auth.access_token)

    async def add_to_cart(
        self, db: AsyncSession, user_id: int, items: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Add items to user's Kroger cart.

        Args:
            db: Database session.
            user_id: User ID.
            items: List of items to add (each with upc, quantity, modality).

        Returns:
            Dictionary with response data.

        Raises:
            KrogerAPIError: If the request fails.
        """
        token = await self.get_user_access_token(db, user_id)

        # Build cart items - only include fields Kroger API accepts
        cart_items = []
        for item in items:
            cart_item = {
                "upc": item["upc"],
                "quantity": item["quantity"],
            }
            # Only add modality if provided
            if "modality" in item and item["modality"]:
                cart_item["modality"] = item["modality"]
            cart_items.append(cart_item)

        payload = {"items": cart_items}
        logger.info("Adding items to Kroger cart. Payload: %s", payload)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(
                    f"{self.base_url}/v1/cart/add",
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                return {"success": True, "items_added": len(items)}

            except httpx.HTTPError as e:
                logger.error("Failed to add items to Kroger cart: %s", e)
                raise KrogerAPIError(f"Add to cart failed: {e}") from e

    async def get_cart(self, db: AsyncSession, user_id: int) -> dict[str, Any]:
        """Get user's current Kroger cart.

        Args:
            db: Database session.
            user_id: User ID.

        Returns:
            Dictionary with cart data.

        Raises:
            KrogerAPIError: If the request fails.
        """
        token = await self.get_user_access_token(db, user_id)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/v1/cart",
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                data = response.json()

                # Extract cart data from response
                cart = data.get("data", {}) if "data" in data else data
                return {
                    "cart_id": cart.get("id"),
                    "items": cart.get("items", []),
                    "total_quantity": cart.get("totalQuantity", 0),
                    "estimated_total": cart.get("estimatedTotal"),
                    "last_modified": cart.get("lastModified"),
                }

            except httpx.HTTPError as e:
                logger.error("Failed to get Kroger cart: %s", e)
                raise KrogerAPIError(f"Get cart failed: {e}") from e


async def get_kroger_service(db: AsyncSession) -> KrogerService:
    """Get Kroger service instance with settings from database.

    Args:
        db: Database session.

    Returns:
        Configured KrogerService instance.
    """
    # Try to get settings from database
    result = await db.execute(select(KrogerSettings))
    settings_obj = result.scalar_one_or_none()

    if settings_obj:
        # Use database settings, falling back to environment variables
        # Use getattr to avoid type issues with SQLAlchemy columns
        client_id = getattr(settings_obj, "client_id", None) or settings.KROGER_CLIENT_ID
        client_secret = getattr(settings_obj, "client_secret", None) or settings.KROGER_CLIENT_SECRET
        oauth_client_id = getattr(settings_obj, "oauth_client_id", None) or settings.KROGER_OAUTH_CLIENT_ID
        oauth_client_secret = (
            getattr(settings_obj, "oauth_client_secret", None) or settings.KROGER_OAUTH_CLIENT_SECRET
        )
        redirect_uri = getattr(settings_obj, "redirect_uri", None) or settings.KROGER_REDIRECT_URI
        base_url = getattr(settings_obj, "base_url", "https://api.kroger.com")

        return KrogerService(
            client_id=client_id,
            client_secret=client_secret,
            oauth_client_id=oauth_client_id,
            oauth_client_secret=oauth_client_secret,
            redirect_uri=redirect_uri,
            base_url=base_url,
        )

    # Fall back to environment variables only
    return KrogerService()


async def get_user_location(db: AsyncSession, user_id: int) -> KrogerUserLocation | None:
    """Get user's saved Kroger location.

    Args:
        db: Database session.
        user_id: User ID.

    Returns:
        KrogerUserLocation or None if not set.
    """
    result = await db.execute(
        select(KrogerUserLocation).where(KrogerUserLocation.user_id == user_id)
    )
    return result.scalar_one_or_none()
