import uuid

import pytest
from sqlalchemy import event as _sa_event
from sqlalchemy.orm import Session

from app.repositories.historical_balance_repository import (
    HistoricalBalanceRepository,
)
from app.repositories.token_repository import TokenRepository
from app.schemas.historical_balance import HistoricalBalanceCreate
from app.schemas.token import TokenCreate
from app.utils.audit import (
    on_after_flush as _audit_on_after_flush,  # type: ignore
)


def _disable_audit_listener(monkeypatch):
    try:
        _sa_event.remove(Session, "after_flush", _audit_on_after_flush)  # type: ignore[arg-type]
    except ValueError:
        pass
    monkeypatch.setattr(
        __import__("app.utils.audit", fromlist=["on_after_flush"]),
        "on_after_flush",
        lambda *a, **k: None,
    )


@pytest.mark.asyncio
async def test_historical_balance_repository_create(db_session, monkeypatch):
    _disable_audit_listener(monkeypatch)

    token = await TokenRepository(db_session).create(
        TokenCreate(
            address=f"0x{uuid.uuid4().hex[:8]}",
            symbol="HIS",
            name="Historical",
            decimals=18,
        )
    )

    hist = await HistoricalBalanceRepository(db_session).create(
        HistoricalBalanceCreate(
            wallet_id=uuid.uuid4(),
            token_id=token.id,
            balance=50.0,
            balance_usd=50.0,
            timestamp=123,
        )
    )
    assert hist.balance_usd == 50.0
