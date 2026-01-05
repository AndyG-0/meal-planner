#!/usr/bin/env python3
"""Script to create or promote a user to admin."""

import asyncio
import sys
from getpass import getpass

# Add parent directory to path
sys.path.insert(0, ".")

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import User
from app.utils.auth import get_password_hash


async def create_admin_user():
    """Create a new admin user or promote existing user."""
    async with AsyncSessionLocal() as db:
        try:
            print("=== Meal Planner Admin User Setup ===\n")

            # Get username
            username = input("Enter username: ").strip()

            if not username:
                print("Error: Username cannot be empty")
                return

            # Check if user exists
            result = await db.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()

            if user:
                print(f"\nUser '{username}' already exists.")
                promote = input("Promote to admin? (y/n): ").strip().lower()

                if promote == "y":
                    user.is_admin = True
                    await db.commit()
                    print(f"\n✓ User '{username}' has been promoted to admin!")
                else:
                    print("No changes made.")
            else:
                print(f"\nUser '{username}' does not exist. Creating new admin user...\n")

                # Get email
                email = input("Enter email: ").strip()
                if not email or "@" not in email:
                    print("Error: Invalid email address")
                    return

                # Check if email already exists
                result = await db.execute(select(User).where(User.email == email))
                if result.scalar_one_or_none():
                    print("Error: Email already registered")
                    return

                # Get password
                password = getpass("Enter password (min 8 characters): ")
                if len(password) < 8:
                    print("Error: Password must be at least 8 characters")
                    return

                confirm_password = getpass("Confirm password: ")
                if password != confirm_password:
                    print("Error: Passwords do not match")
                    return

                # Create admin user
                user = User(
                    username=username,
                    email=email,
                    password_hash=get_password_hash(password),
                    is_admin=True,
                )

                db.add(user)
                await db.commit()
                await db.refresh(user)

                print(f"\n✓ Admin user '{username}' created successfully!")
                print(f"  ID: {user.id}")
                print(f"  Email: {user.email}")
                print(f"  Admin: {user.is_admin}")

        except Exception as e:
            print(f"\nError: {e}")
            await db.rollback()


async def list_admins():
    """List all admin users."""
    async with AsyncSessionLocal() as db:
        try:
            print("=== Current Admin Users ===\n")

            result = await db.execute(select(User).where(User.is_admin))
            admins = result.scalars().all()

            if not admins:
                print("No admin users found.")
            else:
                for admin in admins:
                    print(f"- {admin.username} ({admin.email}) - ID: {admin.id}")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        asyncio.run(list_admins())
    else:
        asyncio.run(create_admin_user())
