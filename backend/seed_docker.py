#!/usr/bin/env python3
"""Script to seed the database with recipes in Docker."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.api.v1.endpoints.recipes import import_seed_recipes
from app.database import AsyncSessionLocal


async def main() -> None:
    """Run the seed import."""
    try:
        async with AsyncSessionLocal() as db:
            result = await import_seed_recipes(db=db)
            print(f"Seeded: {result}")
    except Exception as e:
        print(f"Warning: Seeding failed with error: {e}", file=sys.stderr)
        print("Container startup will continue despite seeding failure.", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
