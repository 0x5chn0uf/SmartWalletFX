import uuid

import pytest

from app.core.config import Settings
from app.core.services import DatabaseService
from app.models import Base
from app.models.user import User
from app.repositories.user_repository_di import UserRepositoryDI
from app.utils.logging import Audit


import pytest_asyncio


@pytest_asyncio.fixture
async def db_service(tmp_path):
    db_file = tmp_path / "test.db"
    settings = Settings(DATABASE_URL=f"sqlite+aiosqlite:///{db_file}")
    service = DatabaseService(settings)
    async with service.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield service
    await service.async_engine.dispose()


@pytest.mark.asyncio
async def test_user_repository_di_crud(db_service):
    repo = UserRepositoryDI(db_service, Audit)
    user = User(
        username=f"alice-{uuid.uuid4().hex[:8]}",
        email=f"alice-{uuid.uuid4().hex[:8]}@example.com",
    )
    saved = await repo.save(user)
    assert saved.id is not None
    by_username = await repo.get_by_username(user.username)
    assert by_username is not None
    assert by_username.email == user.email
    await repo.delete(saved)
    assert await repo.get_by_id(saved.id) is None


@pytest.mark.asyncio
async def test_user_repository_di_exists_and_update(db_service):
    repo = UserRepositoryDI(db_service, Audit)
    user = User(
        username="bob",
        email="bob@example.com",
    )
    saved = await repo.save(user)

    assert await repo.exists(username="bob") is True
    assert await repo.exists(email="bob@example.com") is True
    assert await repo.exists(username="other") is False

    updated = await repo.update(saved, username="robert")
    assert updated.username == "robert"
    await repo.delete(saved)
