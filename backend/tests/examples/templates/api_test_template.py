from dataclasses import dataclass

from tests.fixtures import (
    async_client,
    authenticated_client,
    clean_db_session,
    client,
    mock_httpx_client,
    sync_session,
)


@dataclass
class APITestConfig:
    async_mode: bool = False
    authenticated: bool = False
    use_db: bool = False
    mock_http: bool = False


def get_api_fixtures(config: APITestConfig = None):
    """
    Returns a list of fixtures for API tests based on the provided configuration.
    """
    if config is None:
        config = APITestConfig()
    fixtures = []
    # Choose sync or async client
    fixtures.append(async_client if config.async_mode else client)
    # Optional authentication
    if config.authenticated:
        fixtures.append(authenticated_client)
    # Optional database session
    if config.use_db:
        fixtures.append(clean_db_session if config.async_mode else sync_session)
    # Optional HTTPX mocking
    if config.mock_http:
        fixtures.append(mock_httpx_client)
    return fixtures
