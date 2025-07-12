import pytest
from fastapi import FastAPI

from app.api.endpoints import wallets
from app.core.services import ServiceContainer


def test_wallet_view_uses_container():
    cont = ServiceContainer(load_celery=False)
    router = wallets.get_router(cont)
    app = FastAPI()
    app.include_router(router)
    assert hasattr(router, "routes")
    view = wallets.Wallets(cont)
    assert view.container is cont
