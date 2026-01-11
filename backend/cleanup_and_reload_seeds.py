"""Clean up existing seed recipes and reload them from seed file."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import delete
from sqlalchemy.future import select

from app.database import AsyncSessionLocal
from app.models import Recipe, User
from seed_recipes import load_seed_recipes


async def cleanup_seed_recipes(db) -> int:
    """Delete all seed recipes (recipes owned by the _seed_recipes user)."""
    # Find the seed user
    result = await db.execute(select(User).where(User.username == "_seed_recipes"))
    seed_user = result.scalar_one_or_none()

    if not seed_user:
        print("ℹ️  Seed user not found - no recipes to delete")
        return 0

    # Find all recipes owned by seed user
    result = await db.execute(select(Recipe).where(Recipe.owner_id == seed_user.id))
    recipes_to_delete = result.scalars().all()
    count = len(recipes_to_delete)

    if count > 0:
        # Delete them
        await db.execute(delete(Recipe).where(Recipe.owner_id == seed_user.id))
        await db.commit()
        print(f"✅ Deleted {count} seed recipes")
    else:
        print("ℹ️  No seed recipes found to delete")

    return count


async def main():
    """Main entry point."""
    backend_dir = Path(__file__).parent
    default_seed_file = backend_dir / "data" / "seed_recipes.json"

    seed_file = default_seed_file
    if len(sys.argv) > 1:
        seed_file = Path(sys.argv[1])

    print("🧹 Seed Recipe Cleanup & Reload")
    print("=" * 50)

    try:
        async with AsyncSessionLocal() as db:
            # Step 1: Cleanup
            print("\n📋 Step 1: Cleaning up existing seed recipes...")
            await cleanup_seed_recipes(db)

            # Step 2: Reload
            print("\n📋 Step 2: Loading new seed recipes...")
            success = await load_seed_recipes(db, str(seed_file), dry_run=False)

            if success:
                print("\n✨ Cleanup and reload completed successfully!")
                return 0
            else:
                print("\n❌ Reload failed")
                return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
