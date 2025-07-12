"""
Delete all users from the database (development use only!)
Usage:
    python backend/scripts/delete_all_users.py
"""
import asyncio

from sqlalchemy import delete, select

from app.core.services import ServiceContainer
from app.models.user import User


async def delete_all_users():
    container = ServiceContainer(load_celery=False)
    async with container.db.SessionLocal() as session:
        # Count users before delete
        result = await session.execute(select(User))
        users = result.scalars().all()
        count = len(users)
        if count == 0:
            print("No users to delete.")
            return
        await session.execute(delete(User))
        await session.commit()
        print(f"Deleted {count} users from the database.")


if __name__ == "__main__":
    asyncio.run(delete_all_users())
