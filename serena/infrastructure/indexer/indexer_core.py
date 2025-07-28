"""Core memory indexer functionality."""

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Set

from serena.core.models import extract_task_id_from_path
from serena.services.memory_impl import Memory

from .content_extractors import extract_code_content, extract_title_from_content
from .file_processors import (
    determine_content_kind,
    extract_completion_date,
    extract_status_from_content,
    should_process_file,
)
from .id_generators import (
    generate_code_id,
    generate_design_id,
    generate_doc_id,
    generate_path_based_id,
    generate_readme_id,
)

logger = logging.getLogger(__name__)


class MemoryIndexer:
    """Scans and indexes files from TaskMaster and Serena directories."""

    def __init__(
        self, memory: Optional[Memory] = None, max_workers: int = 4, watcher=None
    ):
        """Initialize the indexer."""
        self.memory = memory or Memory()
        self.max_workers = max_workers
        self.watcher = watcher

        # Default scan directories
        self.scan_dirs = [
            ".taskmaster/memory-bank",
            ".serena/memories",
            "docs",
            "backend/app",
            "frontend/src",
        ]

        # File extensions to index
        self.extensions = {".md", ".txt", ".json", ".py", ".ts", ".tsx"}

        self.strategic_code_paths = {
            "backend/app/models/",
            "backend/app/repositories/",
            "backend/app/services/",
            "backend/app/utils/",
            "backend/app/domain/schemas/",
            "backend/app/api/dependencies.py",
            # Frontend high-value patterns
            "frontend/src/hooks/",
            "frontend/src/components/auth/",
            "frontend/src/services/api.ts",
            "frontend/src/store/",
            "frontend/src/utils/",
        }

        # Track processed files to avoid reprocessing
        self._processed_files: Set[str] = set()

    def scan_directories(
        self,
        directories: Optional[List[str]] = None,
        force_reindex: bool = False,
        show_progress: bool = True,
    ) -> Dict[str, int]:
        """Scan directories for markdown files and index them."""
        if directories is None:
            directories = self.scan_dirs

        stats = {
            "files_found": 0,
            "files_indexed": 0,
            "files_skipped": 0,
            "files_failed": 0,
            "directories_scanned": len(directories),
        }

        files_to_process = []

        for entry in directories:
            logger.info(f"Scanning directory: {entry}")

            p = Path(entry)

            if p.is_file():
                if p.suffix.lower() in self.extensions:
                    files_to_process.append(str(p))
                else:
                    logger.debug(f"Skipping non-supported file: {p}")
                continue

            if not p.exists():
                logger.warning(f"Directory not found: {entry}")
                continue

            for file_path in p.rglob("*"):
                if file_path.suffix.lower() in self.extensions:
                    files_to_process.append(str(file_path))

        if not files_to_process:
            logger.info("No files found to index")
            return stats

        logger.info(f"Found {len(files_to_process)} files to process")

        # Process files with progress tracking
        if show_progress:
            self._process_files_with_progress(files_to_process, force_reindex, stats)
        else:
            self._process_files_batch(files_to_process, force_reindex, stats)

        logger.info(f"Indexing complete: {stats}")
        return stats

    def _process_files_with_progress(
        self, files: List[str], force_reindex: bool, stats: Dict[str, int]
    ) -> None:
        """Process files with progress display."""
        self._process_files(files, force_reindex, stats, show_progress=True)

    def _process_files_batch(
        self, files: List[str], force_reindex: bool, stats: Dict[str, int]
    ) -> None:
        """Process files in parallel batches."""
        self._process_files(files, force_reindex, stats, show_progress=False)

    def _process_files(
        self, files: List[str], force_reindex: bool, stats: Dict[str, int], show_progress: bool = True
    ) -> None:
        """Process files with unified logic for both progress and batch processing."""
        total_files = len(files)
        
        if show_progress:
            # Sequential processing with progress display
            for i, file_path in enumerate(files, 1):
                try:
                    if self._process_single_file(file_path, force_reindex):
                        stats["files_indexed"] += 1
                    else:
                        stats["files_skipped"] += 1

                    # Show progress every 10 files or at end
                    if i % 10 == 0 or i == total_files:
                        progress = (i / total_files) * 100
                        print(
                            f"Progress: {i}/{total_files} ({progress:.1f}%) - "
                            f"Indexed: {stats['files_indexed']}, "
                            f"Skipped: {stats['files_skipped']}"
                        )

                except Exception as e:  # noqa: BLE001
                    logger.error(f"Failed to process {file_path}: {e}")
                    stats["files_failed"] += 1
        else:
            # Parallel processing without progress display
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []

                for file_path in files:
                    future = executor.submit(
                        self._process_single_file, file_path, force_reindex
                    )
                    futures.append((future, file_path))

                # Collect results
                for future, file_path in futures:
                    try:
                        if future.result():
                            stats["files_indexed"] += 1
                        else:
                            stats["files_skipped"] += 1
                    except Exception as e:  # noqa: BLE001
                        logger.error(f"Failed to process {file_path}: {e}")
                        stats["files_failed"] += 1

    def _process_single_file(self, file_path: str, force_reindex: bool) -> bool:
        """Process a single file for indexing."""
        try:
            # Skip if already processed and not forcing reindex
            if file_path in self._processed_files and not force_reindex:
                return False

            # Extract task ID from file path or generate one for docs/design/code
            task_id = extract_task_id_from_path(file_path)
            if not task_id:
                task_id = self._generate_id_for_file(file_path)
                if not task_id:
                    logger.debug(f"Could not extract task ID from {file_path}")
                    return False

            # Check if task already exists and skip if not forcing reindex
            if not force_reindex and self.memory.get(task_id):
                self._processed_files.add(file_path)
                return False

            # Read file content
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_content = f.read()
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to read file {file_path}: {e}")
                return False

            if not raw_content.strip():
                logger.debug(f"Empty file: {file_path}")
                return False

            # Apply smart content extraction for code files
            if file_path.startswith(("backend/", "frontend/")):
                content = extract_code_content(file_path, raw_content)
            else:
                content = raw_content

            # Determine metadata
            kind = determine_content_kind(file_path)
            title = extract_title_from_content(content, file_path)
            status = extract_status_from_content(content)
            completed_at = extract_completion_date(content, file_path)

            # Index the file
            success = self.memory.upsert(
                task_id=task_id,
                markdown_text=content,
                filepath=file_path,
                title=title,
                kind=kind,
                status=status,
                completed_at=completed_at,
            )

            if success:
                self._processed_files.add(file_path)
                logger.debug(f"Indexed {file_path} as task {task_id}")

                # Notify watcher to auto-add directory if configured
                if self.watcher:
                    self.watcher.add_directory_for_file(file_path)

                return True
            else:
                logger.warning(f"Failed to index {file_path}")
                return False

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error processing file {file_path}: {e}")
            return False

    def _generate_id_for_file(self, file_path: str) -> Optional[str]:
        """Generate appropriate ID based on file type and location."""
        # For documentation files, generate ID from path
        if file_path.startswith("docs/"):
            return generate_doc_id(file_path)
        elif file_path.startswith("design/"):
            return generate_design_id(file_path)
        elif file_path.startswith(("backend/", "frontend/")):
            return generate_code_id(file_path)
        elif file_path.startswith((".taskmaster/", ".serena/")):
            # Generate path-based ID for TaskMaster and Serena files
            return generate_path_based_id(file_path, Path(file_path).stem)
        elif Path(file_path).name.lower().startswith("readme"):
            return generate_readme_id(file_path)
        else:
            # Handle other common duplicate filenames
            filename = Path(file_path).stem.lower()
            if filename in ["index", "main", "config", "settings"]:
                return generate_path_based_id(file_path, filename)

        return None

    def watch_directories(self, directories: Optional[List[str]] = None) -> None:
        """Watch directories for changes and auto-index new/modified files."""
        # TODO: Implement file watching with inotify/watchdog
        # For now, this is a placeholder for future enhancement
        logger.info("File watching not yet implemented")
        pass