from __future__ import annotations

"""File indexer for scanning and embedding project files into Serena."""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from serena.core.models import TaskKind, TaskStatus, determine_task_kind, extract_task_id_from_path
from serena.services.memory_impl import Memory

logger = logging.getLogger(__name__)


class MemoryIndexer:
    """Scans and indexes files from TaskMaster and Serena directories."""

    def __init__(
        self, memory: Optional[Memory] = None, max_workers: int = 4, watcher=None
    ):
        """Initialize the indexer.

        Args:
            memory: Memory instance to use for indexing
            max_workers: Maximum number of worker threads for concurrent processing
            watcher: Optional MemoryWatcher to notify when files are indexed
        """
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
        total_files = len(files)

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

    def _process_files_batch(
        self, files: List[str], force_reindex: bool, stats: Dict[str, int]
    ) -> None:
        """Process files in parallel batches."""
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
                # For documentation files, generate ID from path
                if file_path.startswith("docs/"):
                    task_id = self._generate_doc_id(file_path)
                elif file_path.startswith("design/"):
                    task_id = self._generate_design_id(file_path)
                elif file_path.startswith(("backend/", "frontend/")):
                    task_id = self._generate_code_id(file_path)
                elif Path(file_path).name.lower().startswith("readme"):
                    task_id = self._generate_readme_id(file_path)
                else:
                    # Handle other common duplicate filenames
                    filename = Path(file_path).stem.lower()
                    if filename in ["index", "main", "config", "settings"]:
                        task_id = self._generate_path_based_id(file_path, filename)
                    else:
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
                content = self._extract_code_content(file_path, raw_content)
            else:
                content = raw_content

            # Determine metadata
            kind = self._determine_content_kind(file_path)
            title = self._extract_title_from_content(content, file_path)
            status = self._extract_status_from_content(content)
            completed_at = self._extract_completion_date(content, file_path)

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

    def _extract_status_from_content(self, content: str) -> Optional[TaskStatus]:
        """Extract status from file content."""
        content_lower = content.lower()

        # Look for status indicators
        if "status: done" in content_lower or "completed" in content_lower:
            return TaskStatus.DONE
        elif "status: in-progress" in content_lower or "in progress" in content_lower:
            return TaskStatus.IN_PROGRESS
        elif "status: pending" in content_lower:
            return TaskStatus.PENDING
        elif "status: deferred" in content_lower:
            return TaskStatus.DEFERRED
        elif "status: cancelled" in content_lower:
            return TaskStatus.CANCELLED
        elif "status: blocked" in content_lower:
            return TaskStatus.BLOCKED

        # Default assumption based on file type
        if "archive" in content_lower or "reflection" in content_lower:
            return TaskStatus.DONE

        return None

    def _extract_completion_date(
        self, content: str, file_path: str
    ) -> Optional[datetime]:
        """Extract completion date from content or file metadata."""
        # Try to extract from YAML frontmatter
        if content.startswith("---"):
            try:
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    for line in frontmatter.split("\n"):
                        line = line.strip()
                        if line.startswith(("completed:", "date:", "completed_at:")):
                            date_str = line.split(":", 1)[1].strip()
                            return datetime.fromisoformat(date_str.strip("\"'"))
            except Exception:
                pass

        # Look for completion markers in content
        lines = content.split("\n")
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip().lower()
            if "completed:" in line or "finished:" in line:
                try:
                    # Try to extract date from the line
                    date_part = line.split(":", 1)[1].strip()
                    return datetime.fromisoformat(date_part)
                except Exception:
                    pass

        # Fallback to file modification time
        try:
            mtime = Path(file_path).stat().st_mtime
            return datetime.fromtimestamp(mtime)
        except Exception:
            return None

    def _generate_doc_id(self, file_path: str) -> str:
        """Generate a unique ID for documentation files."""
        # Remove 'docs/' prefix and file extension, replace separators with dots
        doc_path = file_path.replace("docs/", "").replace("/", ".").replace("\\", ".")
        if doc_path.endswith(".md"):
            doc_path = doc_path[:-3]
        elif doc_path.endswith(".txt"):
            doc_path = doc_path[:-4]
        elif doc_path.endswith(".json"):
            doc_path = doc_path[:-5]
        return f"doc.{doc_path}"

    def _determine_content_kind(self, file_path: str) -> TaskKind:
        """Determine the content kind based on file path."""
        if file_path.startswith("docs/"):
            return TaskKind.DOC
        elif file_path.startswith("design/"):
            return TaskKind.DOC  # Design tokens are documentation
        elif file_path.startswith(("backend/", "frontend/")):
            return TaskKind.CODE
        elif "archive" in file_path:
            return TaskKind.ARCHIVE
        elif "reflection" in file_path:
            return TaskKind.REFLECTION
        else:
            # Fallback to original function
            return determine_task_kind(file_path)

    def _generate_design_id(self, file_path: str) -> str:
        """Generate a unique ID for design files."""
        # Remove 'design/' prefix and file extension, replace separators with dots
        design_path = (
            file_path.replace("design/", "").replace("/", ".").replace("\\", ".")
        )
        if design_path.endswith(".json"):
            design_path = design_path[:-5]
        return f"design.{design_path}"

    def _generate_readme_id(self, file_path: str) -> str:
        """Generate a unique ID for README files based on their directory path."""
        from pathlib import Path

        path_obj = Path(file_path)

        # If it's in the root, just use "readme"
        if str(path_obj.parent) == "." or path_obj.parent.name == "":
            return "doc-readme"

        # Generate ID based on directory path
        # /project/docs/README.md -> doc-readme.docs
        # /project/backend/README.md -> doc-readme.backend
        # /project/docs/api/README.md -> doc-readme.docs.api
        parent_path = str(path_obj.parent).replace("/", ".").replace("\\", ".")

        # Remove common prefixes to keep IDs clean
        if parent_path.startswith("./"):
            parent_path = parent_path[2:]

        return f"doc-readme.{parent_path}"

    def _generate_path_based_id(self, file_path: str, base_name: str) -> str:
        """Generate a unique ID for common duplicate filenames using directory path."""
        from pathlib import Path

        path_obj = Path(file_path)

        # If it's in the root, just use the base name
        if str(path_obj.parent) == "." or path_obj.parent.name == "":
            return f"doc-{base_name}"

        # Generate ID based on directory path
        # /project/frontend/src/index.ts -> doc-index.frontend.src
        # /project/backend/config.py -> doc-config.backend
        parent_path = str(path_obj.parent).replace("/", ".").replace("\\", ".")

        # Remove common prefixes to keep IDs clean
        if parent_path.startswith("./"):
            parent_path = parent_path[2:]

        return f"doc-{base_name}.{parent_path}"

    def _extract_title_from_content(
        self, content: str, file_path: str = ""
    ) -> Optional[str]:
        """Extract title from file content, with fallback to filename."""
        lines = content.split("\n")

        # Look for first header
        for line in lines[:15]:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
            elif line.startswith("## "):
                return line[3:].strip()

        # Look for title in YAML frontmatter
        if content.startswith("---"):
            try:
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    for line in frontmatter.split("\n"):
                        line = line.strip()
                        if line.startswith("title:"):
                            title = line.split(":", 1)[1].strip()
                            return title.strip("\"'")
            except Exception:
                pass

        # Fallback to filename for docs
        if file_path.startswith("docs/"):
            from pathlib import Path

            return Path(file_path).stem.replace("_", " ").replace("-", " ").title()

        return None

    def _should_process_file(self, file_path: str) -> bool:
        """Determine if a file should be processed based on strategic filtering."""
        # Always process docs and design files
        if file_path.startswith(("docs/", "design/", ".taskmaster/", ".serena/")):
            return True

        # Skip certain patterns
        skip_patterns = [
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".git",
            ".test.",
            "test_",
            "_test.",
            ".spec.",
            ".stories.",
            "dist/",
            "build/",
            ".venv/",
            ".ruff_cache/",
        ]

        if any(pattern in file_path for pattern in skip_patterns):
            return False

        # For code files, check if they match strategic paths
        if file_path.startswith(("backend/", "frontend/")):
            return any(file_path.startswith(path) for path in self.strategic_code_paths)

        return True

    def _generate_code_id(self, file_path: str) -> str:
        """Generate a unique ID for code files."""
        # Normalize path and remove file extension
        code_path = file_path.replace("/", ".").replace("\\", ".")
        if code_path.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
            code_path = code_path.rsplit(".", 1)[0]
        return f"code.{code_path}"

    def _extract_code_content(self, file_path: str, content: str) -> str:
        """Extract smart content from code files based on file type and size."""
        file_size = len(content)

        # For small files (<4KB), embed full content
        if file_size < 4096:
            return self._format_code_content(file_path, content, full_content=True)

        # For larger files, extract metadata
        if file_path.endswith(".py"):
            return self._extract_python_metadata(file_path, content)
        elif file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            return self._extract_typescript_metadata(file_path, content)
        else:
            # Fallback: first part + summary
            lines = content.split("\n")
            return self._format_code_content(
                file_path,
                "\n".join(lines[:50]) + f"\n\n# ... (truncated {len(lines)-50} lines)",
                full_content=False,
            )

    def _format_code_content(
        self, file_path: str, content: str, full_content: bool
    ) -> str:
        """Format code content for embedding with metadata."""
        from pathlib import Path

        filename = Path(file_path).name

        header = f"""# Code: {file_path}
**File**: {filename}
**Type**: {"Full Content" if full_content else "Smart Extract"}
**Size**: {len(content)} characters

## Implementation

```{"python" if file_path.endswith(".py") else "typescript"}
{content}
```"""

        return header

    def _extract_python_metadata(self, file_path: str, content: str) -> str:
        """Extract metadata from Python files."""
        lines = content.split("\n")

        # Extract imports, classes, functions, and docstrings
        imports = []
        classes = []
        functions = []
        current_docstring = None

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Imports
            if line.startswith(("import ", "from ")):
                imports.append(line)

            # Classes
            elif line.startswith("class "):
                class_def = line
                if ":" not in line and i + 1 < len(lines):
                    class_def += " " + lines[i + 1].strip()
                classes.append(class_def)

            # Functions and methods
            elif line.startswith("def ") or "    def " in line:
                func_def = line.strip()
                if ":" not in line and i + 1 < len(lines):
                    func_def += " " + lines[i + 1].strip()
                functions.append(func_def)

            # Module docstring
            elif i < 10 and line.startswith('"""') and current_docstring is None:
                docstring_lines = [line]
                i += 1
                while i < len(lines) and not lines[i].strip().endswith('"""'):
                    docstring_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    docstring_lines.append(lines[i])
                current_docstring = "\n".join(docstring_lines)

            i += 1

        # Format extracted content
        extracted = f"""# Code: {file_path}
**Type**: Python Smart Extract
**Classes**: {len(classes)}
**Functions**: {len(functions)}
**Imports**: {len(imports)}

## Module Documentation
{current_docstring or "No module docstring found"}

## Imports
```python
{chr(10).join(imports[:10])}
{f"... and {len(imports)-10} more imports" if len(imports) > 10 else ""}
```

## Classes
```python
{chr(10).join(classes)}
```

## Functions
```python
{chr(10).join(functions[:15])}
{f"... and {len(functions)-15} more functions" if len(functions) > 15 else ""}
```"""

        return extracted

    def _extract_typescript_metadata(self, file_path: str, content: str) -> str:
        """Extract metadata from TypeScript/JavaScript files."""
        # Limit scan to first 4000 lines – avoids excessive work on megafile bundles
        lines = content.split("\n")[:4000]

        # Extract imports, interfaces, types, components, functions
        imports = []
        interfaces = []
        types = []
        components = []
        functions = []
        exports = []

        for line in lines:
            stripped = line.strip()

            # Imports
            if stripped.startswith("import "):
                imports.append(stripped)

            # Interfaces
            elif stripped.startswith("interface "):
                interfaces.append(stripped)

            # Types
            elif stripped.startswith("type "):
                types.append(stripped)

            # React components (function components)
            elif "const " in stripped and (
                "React.FC" in stripped or "JSX.Element" in stripped
            ):
                components.append(stripped)
            elif stripped.startswith("function ") and (
                "React" in content or "JSX" in content
            ):
                components.append(stripped)

            # Functions
            elif (
                stripped.startswith("function ")
                or stripped.startswith("const ")
                and "=>" in stripped
            ):
                functions.append(stripped)

            # Exports
            elif stripped.startswith("export "):
                exports.append(stripped)

        # If lists are huge, truncate to keep extract compact
        def _truncate(lst, max_items):
            return lst[:max_items], len(lst) - max_items if len(lst) > max_items else 0

        imports_head, imports_more = _truncate(imports, 8)
        interfaces_head, interfaces_more = _truncate(interfaces, 8)
        types_head, types_more = _truncate(types, 8)
        components_head, components_more = _truncate(components, 10)
        functions_head, functions_more = _truncate(functions, 10)

        # Format extracted content
        extracted = f"""# Code: {file_path}
**Type**: TypeScript/JavaScript Smart Extract
**Imports**: {len(imports)}
**Interfaces**: {len(interfaces)}
**Types**: {len(types)}
**Components**: {len(components)}
**Functions**: {len(functions)}

## Imports
```typescript
{chr(10).join(imports_head)}
{f"... and {imports_more} more imports" if imports_more else ""}
```

## Interfaces & Types
```typescript
{chr(10).join(interfaces_head + types_head)}
{f"... and {interfaces_more + types_more} more" if interfaces_more + types_more else ""}
```

## Components
```typescript
{chr(10).join(components_head)}
{f"... and {components_more} more components" if components_more else ""}
```

## Functions
```typescript
{chr(10).join(functions_head)}
{f"... and {functions_more} more functions" if functions_more else ""}
```

## Exports
```typescript
{chr(10).join(exports)}
```"""

        return extracted

    def watch_directories(self, directories: Optional[List[str]] = None) -> None:
        """
        Watch directories for changes and auto-index new/modified files.

        Args:
            directories: Optional list of directories to watch
        """
        # TODO: Implement file watching with inotify/watchdog
        # For now, this is a placeholder for future enhancement
        logger.info("File watching not yet implemented")
        pass


async def index_memories_async(
    directories: Optional[List[str]] = None,
    force_reindex: bool = False,
    max_workers: int = 4,
) -> Dict[str, int]:
    """Async wrapper for memory indexing."""
    import asyncio
    
    indexer = MemoryIndexer(max_workers=max_workers)
    
    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, indexer.scan_directories, directories, force_reindex, True
    )


def index_memories(
    directories: Optional[List[str]] = None,
    force_reindex: bool = False,
    max_workers: int = 4,
    show_progress: bool = True,
) -> Dict[str, int]:
    """Synchronous function to index memories."""
    indexer = MemoryIndexer(max_workers=max_workers)
    return indexer.scan_directories(directories, force_reindex, show_progress) 