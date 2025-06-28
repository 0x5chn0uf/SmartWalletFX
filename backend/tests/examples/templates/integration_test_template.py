from dataclasses import dataclass

from tests.fixtures import async_client, mock_httpx_client, sync_session


@dataclass
class IntegrationTestConfig:
    async_mode: bool = True
    use_db: bool = False
    mock_http: bool = False


def get_integration_fixtures(config: IntegrationTestConfig = None):
    """
    Returns a list of fixtures for integration tests based on the provided configuration.
    """
    if config is None:
        config = IntegrationTestConfig()
    fixtures = []
    # Async client for integration testing
    if config.async_mode:
        fixtures.append(async_client)
    # Optional database session
    if config.use_db:
        fixtures.append(sync_session)
    # Optional HTTPX mocking
    if config.mock_http:
        fixtures.append(mock_httpx_client)
    return fixtures
