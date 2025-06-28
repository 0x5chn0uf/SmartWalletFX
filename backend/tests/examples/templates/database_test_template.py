from dataclasses import dataclass

from tests.fixtures import clean_db_session, sync_session, test_user


@dataclass
class DBTestConfig:
    async_mode: bool = False
    include_user: bool = False


def get_database_fixtures(config: DBTestConfig = None):
    """
    Returns a list of fixtures for database tests based on the provided configuration.
    """
    if config is None:
        config = DBTestConfig()
    fixtures = []
    # Choose transactional or sync session
    fixtures.append(clean_db_session if config.async_mode else sync_session)
    # Optional test user fixture
    if config.include_user:
        fixtures.append(test_user)
    return fixtures
