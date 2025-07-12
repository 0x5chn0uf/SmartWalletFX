import pytest

from app.api.api import api_router
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
    assert cont.endpoints.api_router is api_router
