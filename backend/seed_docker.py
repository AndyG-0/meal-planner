#!/usr/bin/env python3
"""Script to seed the database with recipes in Docker."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.database import AsyncSessionLocal
from app.api.v1.endpoints.recipes import import_seed_recipes


async def main():
    """Run the seed import."""
    async with AsyncSessionLocal() as db:
        result = await import_seed_recipes(db=db)
        print(f"Seeded: {result}")


if __name__ == "__main__":
    asyncio.run(main())