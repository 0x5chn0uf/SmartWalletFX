from __future__ import annotations

"""
Asynchronous write queue used by Memory.upsert.
"""

import logging
import queue
import threading
from typing import Callable, Tuple

logger = logging.getLogger(__name__)


class _WriteQueue:
    """Singleton write queue with one background worker thread."""

    def __init__(self) -> None:
        self._q: "queue.Queue[Tuple[Callable, tuple, dict]]" = queue.Queue()
        self._worker = threading.Thread(
            target=self._run, daemon=True, name="serena-write-queue"
        )
        self._worker.start()

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    def submit(self, fn: Callable, *args, **kwargs) -> None:  # noqa: D401
        """Enqueue *fn*(*args, **kwargs) to be executed in the background."""
        self._q.put((fn, args, kwargs))

    def join(self) -> None:
        """Block until all queued tasks are finished."""
        self._q.join()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _run(self) -> None:  # pragma: no cover – background thread
        while True:
            fn, args, kwargs = self._q.get()
            try:
                fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                logger.error("Write task failed: %s", exc)
            finally:
                self._q.task_done()


# global singleton
write_queue = _WriteQueue()
