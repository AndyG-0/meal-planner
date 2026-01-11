import json
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

# Get version dynamically before any other imports
try:
    import importlib.metadata
    app_version = importlib.metadata.version("meal-planner-backend")
    print(f"DEBUG: App version detected as: {app_version}")
except importlib.metadata.PackageNotFoundError:
    app_version = "unknown"
    print("DEBUG: App version not found, using 'unknown'")

from app.api.v1.endpoints import (
    admin,
    ai,
    auth,
    calendars,
    collections,
    features,
    grocery_lists,
    groups,
    recipes,
)
from app.config import settings
from app.logging_config import setup_logging
from app.middleware.rate_limit import RateLimitMiddleware
from app.models import BlockedImageDomain

# Set up logging
logger = setup_logging(debug=settings.DEBUG)

logger.info(f"Starting {settings.APP_NAME} v{app_version}")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=app_version,
    description="API for meal planning and recipe management",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
try:
    allow_origins = json.loads(settings.BACKEND_CORS_ORIGINS)
except (json.JSONDecodeError, TypeError):
    allow_origins = [origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",")]

logger.debug(f"BACKEND_CORS_ORIGINS raw value: {repr(settings.BACKEND_CORS_ORIGINS)}")
logger.info(f"Parsed CORS allow_origins: {allow_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting (increased for normal browsing usage)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=300,  # Increased from 100 - allows for intensive browsing/filtering
    requests_per_hour=10000,  # Increased from 2000 - allows for extended usage sessions
)

# Create uploads directory and mount static files
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
# Note: Using custom endpoint for uploads instead of StaticFiles to ensure CORS headers
# app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(recipes.router, prefix=settings.API_V1_PREFIX)
app.include_router(calendars.router, prefix=settings.API_V1_PREFIX)
app.include_router(grocery_lists.router, prefix=settings.API_V1_PREFIX)
app.include_router(groups.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai.router, prefix=settings.API_V1_PREFIX)
app.include_router(features.router, prefix=settings.API_V1_PREFIX)
app.include_router(collections.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/uploads/{folder}/{filename}")
async def serve_uploaded_file(folder: str, filename: str) -> Response:
    """Serve uploaded files with proper CORS headers."""
    file_path = Path("uploads") / folder / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Read file content
    content = file_path.read_bytes()

    # Determine content type
    content_type, _ = mimetypes.guess_type(str(file_path))
    if not content_type:
        content_type = "application/octet-stream"

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=86400",
        },
    )


@app.get("/image-proxy")
async def download_image_proxy_test(
    image_url: str = Query(..., description="URL of the image to download"),
    validate_only: bool = Query(False, description="Only validate if image can be downloaded"),
) -> Response:
    """Proxy endpoint to download images from external URLs to avoid CORS issues.

    Can also validate if an image is downloadable without actually downloading it.
    """
    # Extract domain from URL
    try:
        parsed_url = urlparse(image_url)
        domain = parsed_url.netloc.lower().replace("www.", "")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL format"
        )

    # Check if domain is blocked
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(BlockedImageDomain).where(BlockedImageDomain.domain == domain)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Domain {domain} is blocked. Images from this source cannot be downloaded."
            )

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "image/*,*/*",
            "Referer": "https://www.google.com/"
        }

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            if validate_only:
                # Only do a HEAD request to check if image is accessible
                response = await client.head(image_url, headers=headers)
            else:
                response = await client.get(image_url, headers=headers)

            response.raise_for_status()

            if validate_only:
                # Return validation success
                return Response(
                    content=json.dumps({"success": True, "domain": domain}),
                    media_type="application/json",
                    headers={"Access-Control-Allow-Origin": "*"},
                )

            content_type = response.headers.get("content-type", "image/jpeg")

            # Verify it's actually an image
            logger.info("Image URL %s returned content-type: %s", image_url, content_type)
            if not (content_type.startswith("image/") or content_type == "binary/octet-stream"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="URL does not point to an image"
                )

            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Cache-Control": "public, max-age=3600",
                },
            )
    except httpx.HTTPStatusError as e:
        # Auto-block domains that return 403 or other HTTP errors
        logger.warning("Domain %s returned HTTP %s, auto-blocking", domain, e.response.status_code)
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            # Check if already blocked
            result = await db.execute(
                select(BlockedImageDomain).where(BlockedImageDomain.domain == domain)
            )
            if not result.scalar_one_or_none():
                if e.response.status_code == 403:
                    reason = "Auto-blocked: Returned 403 Forbidden"
                else:
                    reason = f"Auto-blocked: Returned HTTP {e.response.status_code}"
                blocked = BlockedImageDomain(
                    domain=domain,
                    reason=reason
                )
                db.add(blocked)
                await db.commit()

        logger.error("Failed to download image from %s: HTTP %s", image_url, e.response.status_code)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download image: HTTP {e.response.status_code} - This source blocks image downloads. Try uploading a file instead.",
        )
    except httpx.HTTPError as e:
        # Auto-block domains that have connection/timeout errors
        logger.warning("Domain %s had connection error, auto-blocking: %s", domain, str(e))
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            # Check if already blocked
            result = await db.execute(
                select(BlockedImageDomain).where(BlockedImageDomain.domain == domain)
            )
            if not result.scalar_one_or_none():
                blocked = BlockedImageDomain(
                    domain=domain,
                    reason=f"Auto-blocked: Connection error ({type(e).__name__})"
                )
                db.add(blocked)
                await db.commit()

        logger.error("Failed to download image from %s: %s", image_url, str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download image: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error downloading image: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download image",
        )



@app.get(f"{settings.API_V1_PREFIX}/recipes/download-image-proxy")
async def download_image_proxy_direct(
    image_url: str = Query(..., description="URL of the image to download"),
) -> Response:
    """Proxy endpoint to download images from external URLs to avoid CORS issues."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(image_url, follow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "image/jpeg")

            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Cache-Control": "public, max-age=3600",
                },
            )
    except httpx.HTTPError as e:
        logger.error("Failed to download image from %s: %s", image_url, str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download image: {str(e)}",
        )
    except Exception as e:
        logger.error("Unexpected error downloading image: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download image",
        )


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Meal Planner API",
        "version": settings.app_version,
        "docs": "/docs",
    }
