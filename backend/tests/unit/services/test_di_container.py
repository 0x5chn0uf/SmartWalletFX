from app.di_container import DIContainer


def test_container_singletons():
    container = DIContainer()
    cfg1 = container.get("config")
    cfg2 = container.get("config")
    assert cfg1 is cfg2

    db1 = container.get("db")
    db2 = container.get("db")
    assert db1 is db2

    assert container.has("config") is True
    assert container.has("missing") is False

    repo1 = container.get("user_repo")
    repo2 = container.get("user_repo")
    assert repo1 is repo2
