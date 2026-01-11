"""Populate database with seed recipes - non-destructive, idempotent import."""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import AsyncSessionLocal
from app.models import Recipe, User
from app.utils.auth import get_password_hash

logger = logging.getLogger(__name__)


def get_default_image_url() -> None:
    """Return None to use the default preview image for recipes without images.

    The frontend will display the default placeholder when image_url is None.
    """
    return None


async def get_or_create_seed_user(db: AsyncSession) -> User:
    """Get or create the seed user for storing seed recipes.

    Admins can edit these recipes because the permission check includes:
    can_edit = recipe.owner_id == current_user.id or current_user.is_admin
    """
    # Check if seed user exists
    result = await db.execute(select(User).where(User.username == "_seed_recipes"))
    user = result.scalar_one_or_none()

    if user:
        return user

    # Create seed user if it doesn't exist
    seed_user = User(
        username="_seed_recipes",
        email="seed@recipes.local",
        password_hash=get_password_hash("seed_password_123"),
        is_admin=False,
    )
    db.add(seed_user)
    await db.commit()
    await db.refresh(seed_user)
    print(f"✅ Created seed user: {seed_user.username}")
    return seed_user


async def load_seed_recipes(db: AsyncSession, seed_file: str, dry_run: bool = False):
    """Load seed recipes from JSON file, non-destructive."""
    # Ensure file exists
    seed_path = Path(seed_file)
    if not seed_path.exists():
        print(f"❌ Seed file not found: {seed_file}")
        return False

    # Load JSON data
    with open(seed_path, encoding="utf-8") as f:
        seed_data = json.load(f)

    print(f"📦 Found {len(seed_data)} recipes in seed file")

    # Get or create seed user
    seed_user = await get_or_create_seed_user(db)

    # Track stats
    created_count = 0
    skipped_count = 0

    # Process each recipe
    for i, recipe_data in enumerate(seed_data, 1):
        # Check if recipe already exists (by title and owner)
        result = await db.execute(
            select(Recipe).where(
                Recipe.title == recipe_data["title"],
                Recipe.owner_id == seed_user.id,
            )
        )
        existing = result.scalars().first()

        if existing:
            skipped_count += 1
            continue

        # Create new recipe
        print(f"  [{i}/{len(seed_data)}] Creating recipe: {recipe_data['title']}", end="\r")
        recipe = Recipe(
            title=recipe_data["title"],
            description=recipe_data.get("description"),
            category=recipe_data.get("category", "staple"),
            owner_id=seed_user.id,  # Owned by seed user, but admins can still edit
            visibility="public",  # Seed recipes are public
            image_url=None,  # Use default preview image
        )

        db.add(recipe)
        created_count += 1

    # Clear the progress line
    print(" " * 80, end="\r")

    # Commit all at once
    if not dry_run:
        await db.commit()
        print(f"✅ Created {created_count} new recipes")
        print(f"⏭️  Skipped {skipped_count} existing recipes")
        print(f"📊 Total recipes in database: {created_count + skipped_count}")
        return True
    else:
        print(f"🔍 [DRY RUN] Would create {created_count} new recipes")
        print(f"🔍 [DRY RUN] Would skip {skipped_count} existing recipes")
        await db.rollback()
        return True


async def main():
    """Main entry point."""
    # Default seed file location
    backend_dir = Path(__file__).parent
    default_seed_file = backend_dir / "data" / "seed_recipes.json"

    # Get seed file from arguments or use default
    dry_run = "--dry-run" in sys.argv
    seed_file = None
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            seed_file = arg
            break

    if not seed_file:
        seed_file = str(default_seed_file)

    print("🌱 Seed Recipes Loader")
    print("=" * 50)
    print(f"📍 Seed file: {seed_file}")
    if dry_run:
        print("🔍 Running in DRY-RUN mode (no changes will be made)")
    print()

    try:
        async with AsyncSessionLocal() as db:
            success = await load_seed_recipes(db, seed_file, dry_run=dry_run)
            if success:
                print("\n✨ Seed operation completed successfully!")
                return 0
            else:
                print("\n❌ Seed operation failed")
                return 1
    except Exception as e:  # noqa: BLE001, F841
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
