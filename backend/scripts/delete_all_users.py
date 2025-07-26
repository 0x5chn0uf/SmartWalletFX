"""
Delete all users from the database (development use only!)
Usage:
    python backend/scripts/delete_all_users.py
"""
import asyncio

from sqlalchemy import delete, select

from app.core.config import Configuration
from app.core.database import CoreDatabase
from app.models.user import User
from app.utils.logging import Audit


async def delete_all_users():
    # Initialize dependencies
    config = Configuration()
    audit = Audit()
    database = CoreDatabase(config, audit)

    async with database.get_session() as session:
        # Count users before delete
        result = await session.execute(select(User))
        users = result.scalars().all()
        count = len(users)
        if count == 0:
            print("No users to delete.")
            return

        print(f"Found {count} users to delete...")

        # Import all models that reference users
        from app.models.historical_balance import HistoricalBalance
        from app.models.token_balance import TokenBalance
        from app.models.transaction import Transaction
        from app.models.wallet import Wallet

        # Delete in proper order to respect foreign key constraints
        print("Deleting historical balances...")
        await session.execute(delete(HistoricalBalance))

        print("Deleting token balances...")
        await session.execute(delete(TokenBalance))

        print("Deleting transactions...")
        await session.execute(delete(Transaction))

        print("Deleting wallets...")
        await session.execute(delete(Wallet))

        # Tables with CASCADE delete don't need explicit deletion:
        # - password_reset (CASCADE)
        # - oauth_account (CASCADE)
        # - email_verification (CASCADE)
        # - refresh_token (CASCADE)

        print("Deleting users...")
        await session.execute(delete(User))

        await session.commit()
        print(
            f"Successfully deleted {count} users and all related data "
            f"from the database."
        )


if __name__ == "__main__":
    asyncio.run(delete_all_users())
