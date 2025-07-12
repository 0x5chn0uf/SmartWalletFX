import pytest

from app.api.api import create_api_router
from app.core.services import ServiceContainer
from app.repositories.user_repository import UserRepository
from app.usecase.wallet_usecase import WalletUsecase


def test_repository_singletons():
    cont = ServiceContainer(load_celery=False)
    repo = cont.repositories.UserRepository
    assert isinstance(repo, UserRepository)


def test_usecase_singletons():
    cont = ServiceContainer(load_celery=False)
    assert cont.usecases.WalletUsecase is WalletUsecase


def test_endpoint_singleton():
    cont = ServiceContainer(load_celery=False)
    api_router = create_api_router(cont)
    assert list(cont.endpoints.api_router.routes)[0].path == list(api_router.routes)[0].path
