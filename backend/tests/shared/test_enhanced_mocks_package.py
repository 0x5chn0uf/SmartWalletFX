import pytest

from tests.shared.fixtures.enhanced_mocks import MockBehavior, MockServiceFactory
from app.domain.schemas.user import UserCreate


@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_repository_tracking_and_failure():
    repo = MockServiceFactory.create_user_repository()
    await repo.create(
        UserCreate(
            username="user1", email="u1@example.com", password="StrongPassword123!"
        )
    )
    await repo.create(
        UserCreate(
            username="user2", email="u2@example.com", password="StrongPassword123!"
        )
    )

    assert len(repo.get_calls("create")) == 2

    repo.set_behavior(MockBehavior.FAILURE)
    with pytest.raises(ValueError):
        await repo.create(
            UserCreate(
                username="user3", email="u3@example.com", password="StrongPassword123!"
            )
        )

    assert repo.get_calls("create")[-1].exception is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_email_service_tracking_and_failure():
    service = MockServiceFactory.create_email_service()
    assert await service.send_verification_email("test@example.com", "tok1")
    service.set_behavior(MockBehavior.FAILURE)
    assert not await service.send_verification_email("test@example.com", "tok2")

    calls = service.get_calls("send_verification_email")
    assert len(calls) == 2
    assert calls[1].result is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_upload_service_tracking_and_failure():
    service = MockServiceFactory.create_file_upload_service()
    url = await service.upload_profile_picture("user1", b"data", "a.png")
    assert url in service.uploaded_files
    await service.delete_profile_picture(url)
    assert len(service.get_calls("delete_profile_picture")) == 1

    service.set_behavior(MockBehavior.FAILURE)
    with pytest.raises(ValueError):
        await service.upload_profile_picture("user1", b"d", "b.png")

    assert service.get_calls("upload_profile_picture")[-1].exception is not None
