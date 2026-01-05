#!/usr/bin/env python3
"""Test script for URL fetching functionality."""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import OpenAIService lazily inside the function to avoid pytest import-time
# failures when optional dependencies (e.g., beautifulsoup4) are not installed.
# We will attempt the import at runtime in the function and fail gracefully.

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def fetch_url(url: str):
    """Fetch a URL without needing database. Not a pytest test function."""
    logger.info(f"Fetching URL: {url}")

    # Create a minimal service instance (won't actually use DB for fetch_url)
    try:
        from app.services.openai_service import OpenAIService
    except Exception as e:
        logger.error("OpenAIService import failed: %s", e)
        return None

    service = OpenAIService(None)  # type: ignore

    try:
        result = await service.fetch_url(url)

        print("\n" + "=" * 80)
        print("FETCH RESULT")
        print("=" * 80)
        print(f"\nTitle: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"\nContent ({len(result['content'])} characters):")
        print("-" * 80)
        print(result["content"])
        print("-" * 80)

        return result

    except Exception as e:
        logger.error(f"Failed to fetch URL: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_url_fetch.py <URL>")
        print("\nExample:")
        print(
            "  python test_url_fetch.py 'https://www.fornobravo.com/pizza-oven-library/article/pizza-sequence/pizza-dough/?srsltid=AfmBOopyz6OEPwZ8pzs43V1b8lh1Nb1OhuTI6J_-yXog5f8WsMcaT2sy'"
        )
        sys.exit(1)

    url = sys.argv[1]
    asyncio.run(fetch_url(url))
