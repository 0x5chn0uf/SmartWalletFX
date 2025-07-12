from __future__ import annotations

from typing import Any, Dict

from app.core.services import ConfigurationService, DatabaseService
from app.repositories.user_repository_di import UserRepositoryDI
from app.utils.logging import Audit


class DIContainer:
    """Minimal dependency injection container for singletons."""

    def __init__(self) -> None:
        self._services: Dict[str, Any] = {}
        self._setup_core()
        self._setup_repositories()

    # ------------------------------------------------------------------
    # Service registration helpers
    # ------------------------------------------------------------------
    def register(self, name: str, svc: Any) -> None:
        self._services[name] = svc

    def get(self, name: str) -> Any:
        return self._services[name]

    def has(self, name: str) -> bool:
        """Return True if *name* is registered."""
        return name in self._services

    # ------------------------------------------------------------------
    # Bootstrapping
    # ------------------------------------------------------------------
    def _setup_core(self) -> None:
        config = ConfigurationService()
        self.register("config", config)

        db = DatabaseService(config.settings)
        self.register("db", db)

    def _setup_repositories(self) -> None:
        db = self.get("db")
        user_repo = UserRepositoryDI(db, Audit)
        self.register("user_repo", user_repo)

