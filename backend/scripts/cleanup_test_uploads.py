#!/usr/bin/env python3
"""Manual cleanup script for test upload files."""

import sys
from pathlib import Path


def cleanup_test_uploads(dry_run: bool = False):
    """Clean up test upload files."""
    backend_dir = Path(__file__).parent.parent
    uploads_dir = backend_dir / "uploads" / "profile_pictures"

    if not uploads_dir.exists():
        print("Upload directory does not exist.")
        return

    removed_count = 0
    total_size = 0

    for file_path in uploads_dir.glob("*"):
        if file_path.is_file():
            filename = file_path.name
            file_size = file_path.stat().st_size

            # Criteria for test files
            should_remove = (
                "MagicMock" in filename
                or filename.startswith("test_")
                or filename.startswith("dummy_")
                or filename.startswith("temp_")
                or file_size < 100  # Very small files likely test artifacts
            )

            if should_remove:
                if dry_run:
                    print(f"Would remove: {filename} ({file_size} bytes)")
                else:
                    try:
                        file_path.unlink()
                        print(f"Removed: {filename} ({file_size} bytes)")
                    except OSError as e:
                        print(f"Failed to remove {filename}: {e}")
                        continue

                removed_count += 1
                total_size += file_size

    if removed_count == 0:
        print("No test files found to clean up.")
    else:
        action = "Would remove" if dry_run else "Removed"
        print(f"\n{action} {removed_count} test files ({total_size} bytes total)")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN - No files will be deleted\n")

    cleanup_test_uploads(dry_run=dry_run)
