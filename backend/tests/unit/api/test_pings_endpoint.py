from fastapi import FastAPI

from app.api.endpoints import pings
from app.core.services import ServiceContainer


def test_pings_view_uses_container():
    cont = ServiceContainer(load_celery=False)
    router = pings.get_router(cont)

    app = FastAPI()
    app.include_router(router)
    assert hasattr(router, 'routes')
    view = pings.Pings(cont)
    assert view.container is cont
