import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
from app.middleware.rate_limit import RateLimitMiddleware

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for meal planning and recipe management",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
try:
    allow_origins = json.loads(settings.BACKEND_CORS_ORIGINS)
except (json.JSONDecodeError, TypeError):
    allow_origins = [origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",")]

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
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Meal Planner API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
