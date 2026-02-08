"""Seed Kroger brand URLs for the Kroger Family of Companies.

This script populates the kroger_brand_urls table with all known Kroger brands
and their respective cart and checkout URLs.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import KrogerBrandUrls


# Kroger Family of Companies with their respective URLs
# Based on https://www.kroger.com/i/kroger-family-of-companies
KROGER_BRANDS = [
    {
        "brand": "KROGER",
        "display_name": "Kroger",
        "cart_url": "https://www.kroger.com/cart",
        "checkout_url": "https://www.kroger.com/checkout",
    },
    {
        "brand": "RALPHS",
        "display_name": "Ralphs",
        "cart_url": "https://www.ralphs.com/cart",
        "checkout_url": "https://www.ralphs.com/checkout",
    },
    {
        "brand": "FRED MEYER",
        "display_name": "Fred Meyer",
        "cart_url": "https://www.fredmeyer.com/cart",
        "checkout_url": "https://www.fredmeyer.com/checkout",
    },
    {
        "brand": "KING SOOPERS",
        "display_name": "King Soopers",
        "cart_url": "https://www.kingsoopers.com/cart",
        "checkout_url": "https://www.kingsoopers.com/checkout",
    },
    {
        "brand": "SMITH'S FOOD AND DRUG",
        "display_name": "Smith's Food and Drug",
        "cart_url": "https://www.smithsfoodanddrug.com/cart",
        "checkout_url": "https://www.smithsfoodanddrug.com/checkout",
    },
    {
        "brand": "FRY'S",
        "display_name": "Fry's",
        "cart_url": "https://www.frysfood.com/cart",
        "checkout_url": "https://www.frysfood.com/checkout",
    },
    {
        "brand": "DILLONS",
        "display_name": "Dillons",
        "cart_url": "https://www.dillons.com/cart",
        "checkout_url": "https://www.dillons.com/checkout",
    },
    {
        "brand": "CITY MARKET",
        "display_name": "City Market",
        "cart_url": "https://www.citymarket.com/cart",
        "checkout_url": "https://www.citymarket.com/checkout",
    },
    {
        "brand": "QFC",
        "display_name": "QFC",
        "cart_url": "https://www.qfc.com/cart",
        "checkout_url": "https://www.qfc.com/checkout",
    },
    {
        "brand": "BAKER'S",
        "display_name": "Baker's",
        "cart_url": "https://www.shopbakers.com/cart",
        "checkout_url": "https://www.shopbakers.com/checkout",
    },
    {
        "brand": "FOOD 4 LESS",
        "display_name": "Food 4 Less",
        "cart_url": "https://www.food4less.com/cart",
        "checkout_url": "https://www.food4less.com/checkout",
    },
    {
        "brand": "FOODS CO",
        "display_name": "Foods Co",
        "cart_url": "https://www.foodsco.net/cart",
        "checkout_url": "https://www.foodsco.net/checkout",
    },
    {
        "brand": "GERBES",
        "display_name": "Gerbes",
        "cart_url": "https://www.gerbes.com/cart",
        "checkout_url": "https://www.gerbes.com/checkout",
    },
    {
        "brand": "JAY C FOOD STORE",
        "display_name": "Jay C Food Store",
        "cart_url": "https://www.jaycfoods.com/cart",
        "checkout_url": "https://www.jaycfoods.com/checkout",
    },
    {
        "brand": "MARIANO'S",
        "display_name": "Mariano's",
        "cart_url": "https://www.marianos.com/cart",
        "checkout_url": "https://www.marianos.com/checkout",
    },
    {
        "brand": "METRO MARKET",
        "display_name": "Metro Market",
        "cart_url": "https://www.metromarket.net/cart",
        "checkout_url": "https://www.metromarket.net/checkout",
    },
    {
        "brand": "PAY-LESS SUPER MARKETS",
        "display_name": "Pay-Less Super Markets",
        "cart_url": "https://www.pay-less.com/cart",
        "checkout_url": "https://www.pay-less.com/checkout",
    },
    {
        "brand": "PICK'N SAVE",
        "display_name": "Pick'n Save",
        "cart_url": "https://www.picknsave.com/cart",
        "checkout_url": "https://www.picknsave.com/checkout",
    },
    {
        "brand": "RULER",
        "display_name": "Ruler",
        "cart_url": "https://www.rulerfoods.com/cart",
        "checkout_url": "https://www.rulerfoods.com/checkout",
    },
]


async def seed_kroger_brands():
    """Seed the Kroger brand URLs into the database."""
    # Create async engine and session
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check existing brands
        result = await session.execute(select(KrogerBrandUrls))
        existing_brands = {brand.brand: brand for brand in result.scalars().all()}

        added = 0
        updated = 0
        skipped = 0

        for brand_data in KROGER_BRANDS:
            brand_name = brand_data["brand"]

            if brand_name in existing_brands:
                # Update existing brand
                existing = existing_brands[brand_name]
                existing.display_name = brand_data["display_name"]
                existing.cart_url = brand_data["cart_url"]
                existing.checkout_url = brand_data["checkout_url"]
                existing.is_active = True
                updated += 1
                print(f"Updated: {brand_name}")
            else:
                # Create new brand
                new_brand = KrogerBrandUrls(
                    brand=brand_name,
                    display_name=brand_data["display_name"],
                    cart_url=brand_data["cart_url"],
                    checkout_url=brand_data["checkout_url"],
                    is_active=True,
                )
                session.add(new_brand)
                added += 1
                print(f"Added: {brand_name}")

        await session.commit()

        print(f"\n✅ Seeding complete!")
        print(f"   Added: {added}")
        print(f"   Updated: {updated}")
        print(f"   Skipped: {skipped}")

    await engine.dispose()


if __name__ == "__main__":
    print("🌱 Seeding Kroger brand URLs...")
    print(f"   Total brands to process: {len(KROGER_BRANDS)}\n")
    asyncio.run(seed_kroger_brands())
