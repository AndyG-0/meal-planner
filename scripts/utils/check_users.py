"""Check users in database."""

import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import User


async def check_users():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        print(f"Found {len(users)} users:")
        for u in users:
            print(f"  - {u.username} ({u.email}) - deleted_at={u.deleted_at}")


if __name__ == "__main__":
    asyncio.run(check_users())
