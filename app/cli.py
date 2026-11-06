"""Command-line interface for administrative operations (e.g. creating administrators)."""

import argparse
import asyncio
import getpass
import sys

from sqlalchemy import select

from app.config import get_settings
from app.database.session import close_database, create_session_maker, init_db_engine
from app.models.admin_user import AdminUser
from app.security.password import hash_password


async def create_admin(username: str, password: str) -> None:
    """Create a new administrator account in the database."""
    settings = get_settings()
    engine = init_db_engine(settings.DATABASE_URL)
    session_maker = create_session_maker(engine)

    try:
        async with session_maker() as session:
            # Check if username exists
            existing = await session.execute(
                select(AdminUser).where(AdminUser.username == username)
            )
            if existing.scalar_one_or_none():
                print(f"Error: Admin user '{username}' already exists.", file=sys.stderr)
                sys.exit(1)

            hashed = hash_password(password)
            admin = AdminUser(
                username=username,
                password_hash=hashed,
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            print(f"Success: Administrator '{username}' created successfully (ID: {admin.id}).")
    finally:
        await close_database(engine)


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Telegram Video Platform Admin CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create-admin command
    create_parser = subparsers.add_parser("create-admin", help="Create a new administrator account")
    create_parser.add_argument("--username", "-u", required=True, help="Administrator username")
    create_parser.add_argument("--password", "-p", help="Administrator password (prompted if omitted)")

    args = parser.parse_args()

    if args.command == "create-admin":
        username = args.username.strip()
        if not username:
            print("Error: Username cannot be empty.", file=sys.stderr)
            sys.exit(1)

        password = args.password
        if not password:
            password = getpass.getpass(f"Enter password for admin '{username}': ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Error: Passwords do not match.", file=sys.stderr)
                sys.exit(1)

        if len(password) < 8:
            print("Error: Password must be at least 8 characters long.", file=sys.stderr)
            sys.exit(1)

        asyncio.run(create_admin(username, password))


if __name__ == "__main__":
    main()

