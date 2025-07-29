# -*- coding: utf-8 -*-
"""File-watcher for Serena"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

from watchdog.events import FileSystemEventHandler  # noqa: WPS433
from watchdog.observers import Observer

from serena.core.models import (Archive, Embedding, compute_content_hash,
                                determine_task_kind, extract_task_id_from_path)
from serena.database.session import get_session



class _SerenaEventHandler(FileSystemEventHandler):
    """Handle FS events and dispatch to the parent watcher."""

    def __init__(self, watcher: "_WatchdogMemoryWatcher") -> None:
        super().__init__()
        self._watcher = watcher

    def on_modified(self, event):  # noqa: D401, ANN001
        if event.is_directory:
            return
        self._watcher.process_change(event.src_path)

    def on_created(self, event):  # noqa: D401, ANN001
        if event.is_directory:
            return
        self._watcher.process_change(event.src_path)

    def on_deleted(self, event):  # noqa: D401, ANN001
        if event.is_directory:
            return
        self._watcher.process_deletion(event.src_path)


class _WatchdogMemoryWatcher:
    """Observes markdown archives and keeps the memory index up-to-date."""

    def __init__(
        self,
        *,
        memory,  # Local Memory or RemoteMemory shim
        auto_add_taskmaster: bool = True,
        callback: Optional[Callable[[str, str, str], None]] = None,
    ) -> None:
        self.memory = memory
        self.auto_add_taskmaster = auto_add_taskmaster
        self.callback = callback or (lambda *_: None)

        self._running = False
        self._observer: Optional[Observer] = None

        # path -> metadata (task_id, sha256)
        self._tracked: Dict[str, Dict[str, str]] = {}

        self._setup_tracking()

    @property
    def watched_paths(self) -> List[str]:  # noqa: D401
        """List of directories being watched (for CLI display)."""

        dirs: Set[str] = {str(Path(p).parent) for p in self._tracked.keys()}
        return sorted(dirs)

    def start(self, catch_up: bool = True):  # noqa: D401, ANN001
        """Start the observer thread."""

        if self._running:
            return

        if not self._tracked:
            print("No files/directories to watch – falling back to no-op")
            return

        # Perform offline catch-up scan BEFORE starting observer so that we
        # don’t miss rapid edits during startup.
        if catch_up:
            self._initial_crawl()

        self._observer = Observer()
        handler = _SerenaEventHandler(self)

        for directory in self.watched_paths:
            self._observer.schedule(handler, path=directory, recursive=True)

        self._observer.start()
        self._running = True

    def stop(self):  # noqa: D401
        if not self._running or self._observer is None:
            return

        self._observer.stop()
        self._observer.join(timeout=5)
        self._running = False

    def is_running(self) -> bool:  # noqa: D401
        return self._running

    def _setup_tracking(self) -> None:
        """Populate *self._tracked* with existing archives."""

        db_path = getattr(self.memory, "db_path", None)
        if db_path and Path(db_path).exists():
            try:
                with get_session(db_path) as session:
                    archives = session.query(Archive).all()
                    for archive in archives:
                        if archive.filepath:
                            self._tracked[archive.filepath] = {
                                "task_id": archive.task_id,
                                "sha256": archive.sha256 or "",
                            }
            except Exception as exc:
                print("Failed to load existing archives: %s", exc)

        if self.auto_add_taskmaster:
            from serena.cli.common import \
                detect_taskmaster_directories  # lazy import

            for directory in detect_taskmaster_directories():
                for md_file in Path(directory).rglob("*.md"):
                    task_id = extract_task_id_from_path(str(md_file)) or str(
                        md_file.stem
                    )
                    self._tracked[str(md_file)] = {
                        "task_id": task_id,
                        "sha256": "",  # Unknown until computed
                    }

    def _initial_crawl(self) -> None:
        """Detect changes that occurred while the watcher was offline."""

        print("Running initial crawl across %d files", len(self._tracked))
        for path in list(self._tracked.keys()):
            if Path(path).exists():
                self._maybe_upsert(path, initial_scan=True)
            else:
                self.process_deletion(path)

    def process_change(self, path: str) -> None:  # noqa: D401
        self._maybe_upsert(path, initial_scan=False)

    def process_deletion(self, path: str) -> None:  # noqa: D401
        meta = self._tracked.pop(path, None)
        if not meta:
            return  # Not tracked – ignore

        task_id = meta["task_id"]

        deleted = False

        if hasattr(self.memory, "delete"):
            try:
                deleted = bool(self.memory.delete(task_id))  # type: ignore[arg-type]
            except Exception as exc:  # noqa: BLE001
                print("Backend delete failed for %s: %s", task_id, exc)
        else:
            # Local DB path – use ORM for deletion
            db_path = getattr(self.memory, "db_path", None)
            if db_path and Path(db_path).exists():
                try:
                    with get_session(db_path) as session:
                        archive = (
                            session.query(Archive).filter_by(task_id=task_id).first()
                        )
                        if archive:
                            session.delete(archive)
                            session.commit()
                            deleted = True
                except Exception as exc:
                    print("Local delete failed for %s: %s", task_id, exc)

        if deleted:
            print("Deleted task %s due to file removal", task_id)
            self.callback("deleted", task_id, path)

    def _maybe_upsert(self, path: str, *, initial_scan: bool) -> None:
        """Upsert file *path* if its hash changed since last index."""

        if not Path(path).exists():
            return

        try:
            content = Path(path).read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            print("Unable to read %s: %s", path, exc)
            return

        sha256 = compute_content_hash(content)

        meta = self._tracked.get(path)
        if meta and meta.get("sha256") == sha256:
            return  # No change

        task_id = (
            meta["task_id"]
            if meta
            else extract_task_id_from_path(path) or Path(path).stem
        )

        kind = determine_task_kind(path)

        try:
            self.memory.upsert(task_id, content, filepath=str(path), kind=kind)
            # Update tracking info
            self._tracked[path] = {"task_id": task_id, "sha256": sha256}

            action = "indexed" if initial_scan else "modified"
            self.callback(action, task_id, path)
            print("Upserted %s (%s)", task_id, action)
        except Exception as exc:  # noqa: BLE001
            print("Upsert failed for %s: %s", path, exc)


def create_memory_watcher(
    *, memory, auto_add_taskmaster: bool = True, callback=None
):  # noqa: ANN001
    """Create a :class:`_WatchdogMemoryWatcher` instance.

    *watchdog* is a hard dependency; if the import at module-import time failed
    an :class:`ImportError` would already have been raised, so reaching this
    function guarantees the dependency is present.
    """

    return _WatchdogMemoryWatcher(
        memory=memory, auto_add_taskmaster=auto_add_taskmaster, callback=callback
    )


__all__ = [
    "create_memory_watcher"
]
