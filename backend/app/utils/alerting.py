"""Alerting helper – send critical notifications to Slack (or other)."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

import httpx

_logger = logging.getLogger("alerting")

_SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack_alert(message: str, **attachments: Any) -> None:
    """Send *message* to Slack webhook if configured.

    If no webhook is configured, the alert is logged at *warning* level instead.
    Errors during send are caught and logged to avoid crashing the caller.
    """

    if not _SLACK_WEBHOOK_URL:
        _logger.warning("Slack webhook not configured – alert: %s", message)
        return

    payload: Dict[str, Any] = {"text": message}
    if attachments:
        payload["attachments"] = [attachments]  # type: ignore[assignment]

    try:
        resp = httpx.post(_SLACK_WEBHOOK_URL, json=payload, timeout=5)
        resp.raise_for_status()
    except Exception as exc:  # pragma: no cover
        _logger.error("Failed to send Slack alert: %s", exc)
