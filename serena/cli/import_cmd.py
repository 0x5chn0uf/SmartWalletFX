from __future__ import annotations

"""Bulk import command for efficiently importing archives and documents."""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from serena.core.models import TaskKind, TaskStatus
from serena.infrastructure.write_queue import WriteOperationType
from serena.settings import settings

logger = logging.getLogger(__name__)


def _parse_import_format(file_path: Path) -> Optional[str]:
    """Detect the format of import file based on extension and content."""
    extension = file_path.suffix.lower()
    
    if extension == '.json':
        return 'json'
    elif extension in ['.jsonl', '.ndjson']:
        return 'jsonlines'
    elif extension == '.csv':
        return 'csv'
    else:
        # Try to detect format from content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('{'):
                    # Could be JSON or JSONL
                    f.seek(0)
                    content = f.read()
                    try:
                        json.loads(content)
                        return 'json'
                    except json.JSONDecodeError:
                        return 'jsonlines'
                elif first_line.startswith('['):
                    return 'json'
        except Exception:
            pass
    
    return None


def _load_json_import(file_path: Path) -> List[Dict[str, Any]]:
    """Load data from JSON format."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Single record
        return [data]
    else:
        raise ValueError("JSON must contain an array or single object")


def _load_jsonlines_import(file_path: Path) -> List[Dict[str, Any]]:
    """Load data from JSON Lines format."""
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append(record)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON on line {line_num}: {e}")
                continue
    
    return records


def _load_csv_import(file_path: Path) -> List[Dict[str, Any]]:
    """Load data from CSV format."""
    try:
        import csv
    except ImportError:
        raise ImportError("CSV support requires Python's csv module")
    
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Clean empty values
            cleaned_row = {k: v for k, v in row.items() if v.strip()}
            if cleaned_row:
                records.append(cleaned_row)
    
    return records


def _validate_import_record(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Validate and normalize an import record."""
    # Required fields
    if 'task_id' not in record:
        logger.warning("Record missing required 'task_id' field, skipping")
        return None
    
    if 'content' not in record and 'markdown_text' not in record:
        logger.warning(f"Record {record['task_id']} missing content field, skipping")
        return None
    
    # Normalize content field name
    if 'content' in record:
        record['markdown_text'] = record.pop('content')
    
    # Validate and convert status
    if 'status' in record and isinstance(record['status'], str):
        try:
            record['status'] = TaskStatus(record['status'])
        except ValueError:
            logger.warning(f"Invalid status '{record['status']}' for task {record['task_id']}")
            record['status'] = None
    
    # Validate and convert kind
    if 'kind' in record and isinstance(record['kind'], str):
        try:
            record['kind'] = TaskKind(record['kind'])
        except ValueError:
            logger.warning(f"Invalid kind '{record['kind']}' for task {record['task_id']}")
            record['kind'] = TaskKind.ARCHIVE
    
    # Convert datetime strings
    if 'completed_at' in record and isinstance(record['completed_at'], str):
        try:
            from datetime import datetime
            record['completed_at'] = datetime.fromisoformat(record['completed_at'])
        except ValueError:
            logger.warning(f"Invalid date format for task {record['task_id']}")
            record['completed_at'] = None
    
    return record


def _prepare_bulk_operations(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepare records for bulk import operations."""
    operations = []
    
    for record in records:
        validated = _validate_import_record(record)
        if validated:
            operations.append(validated)
    
    return operations


def _try_server_import(operations: List[Dict[str, Any]]) -> bool:
    """Try to use server API for bulk import."""
    import requests
    
    server_url = settings.server_url
    
    try:
        response = requests.post(
            f"{server_url}/archives/bulk",
            json={"operations": operations},
            timeout=30
        )
        return response.status_code == 200
    except Exception as exc:
        logger.debug("Server import failed: %s", exc, exc_info=True)
    
    return False


def _local_bulk_import(
    operations: List[Dict[str, Any]], 
    db_path: Optional[str] = None,
    use_async: bool = True,
    batch_size: int = 50
) -> Dict[str, int]:
    """Perform bulk import using local Memory service with write queue."""
    stats = {
        "total": len(operations),
        "successful": 0,
        "failed": 0,
        "batches": 0
    }
    
    try:
        memory = Memory(db_path=db_path)
        
        # Process in batches for better performance
        for i in range(0, len(operations), batch_size):
            batch = operations[i:i + batch_size]
            stats["batches"] += 1
            
            try:
                if use_async and settings.async_write:
                    # Use async batch processing
                    operation_ids = memory.batch_upsert(batch, async_write=True)
                    stats["successful"] += len(operation_ids)
                    logger.info(f"Batch {stats['batches']}: queued {len(operation_ids)} operations")
                else:
                    # Use synchronous batch processing
                    results = memory.batch_upsert(batch, async_write=False)
                    stats["successful"] += len(results)
                    logger.info(f"Batch {stats['batches']}: processed {len(results)} operations")
                    
            except Exception as exc:
                logger.error(f"Batch {stats['batches']} failed: {exc}")
                stats["failed"] += len(batch)
        
        return stats
        
    except Exception as exc:
        logger.error("Bulk import failed: %s", exc, exc_info=True)
        stats["failed"] = stats["total"] - stats["successful"]
        return stats


def cmd_import(args) -> None:
    """Import archives and documents from various file formats."""
    logger.info("Starting bulk import operation")
    
    try:
        # Validate input file
        input_file = Path(args.file)
        if not input_file.exists():
            print(f"❌ Input file not found: {input_file}")
            sys.exit(1)
        
        if not input_file.is_file():
            print(f"❌ Path is not a file: {input_file}")
            sys.exit(1)
        
        # Detect format
        format_type = _parse_import_format(input_file)
        if not format_type:
            print(f"❌ Unable to detect file format for: {input_file}")
            print("   Supported formats: JSON (.json), JSON Lines (.jsonl), CSV (.csv)")
            sys.exit(1)
        
        print(f"📂 Loading data from {input_file} (format: {format_type})")
        
        # Load data based on format
        start_time = time.time()
        
        if format_type == 'json':
            records = _load_json_import(input_file)
        elif format_type == 'jsonlines':
            records = _load_jsonlines_import(input_file)
        elif format_type == 'csv':
            records = _load_csv_import(input_file)
        else:
            print(f"❌ Unsupported format: {format_type}")
            sys.exit(1)
        
        load_time = time.time() - start_time
        print(f"📊 Loaded {len(records)} records in {load_time:.2f}s")
        
        if not records:
            print("⚠️  No records found in input file")
            return
        
        # Prepare operations
        print("🔍 Validating and preparing import operations...")
        operations = _prepare_bulk_operations(records)
        
        if not operations:
            print("❌ No valid operations after validation")
            sys.exit(1)
        
        skipped = len(records) - len(operations)
        if skipped > 0:
            print(f"⚠️  Skipped {skipped} invalid records")
        
        print(f"✅ Prepared {len(operations)} valid operations")
        
        # Perform import
        print("🚀 Starting bulk import...")
        import_start = time.time()
        
        # Server mode only - fail if server not available
        success = False
        
        if _try_server_import(operations):
            print("   ⚡ Imported via server API")
            success = True
            stats = {"total": len(operations), "successful": len(operations), "failed": 0}
        else:
            print("❌ Server not available - only remote operations are supported")
            sys.exit(1)
        
        import_time = time.time() - import_start
        total_time = time.time() - start_time
        
        # Display results
        print(f"\n📈 Import Results:")
        print(f"   Total records: {stats['total']}")
        print(f"   Successful: {stats['successful']}")
        print(f"   Failed: {stats['failed']}")
        if 'batches' in stats:
            print(f"   Batches processed: {stats['batches']}")
        print(f"   Import time: {import_time:.2f}s")
        print(f"   Total time: {total_time:.2f}s")
        
        if stats['successful'] > 0:
            rate = stats['successful'] / import_time if import_time > 0 else 0
            print(f"   Import rate: {rate:.1f} records/sec")
        
        if success:
            print(f"✅ Bulk import completed successfully!")
            if use_async and settings.async_write and stats['failed'] == 0:
                print("⏳ Operations queued for background processing")
        else:
            print(f"❌ Bulk import failed")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n🛑 Import cancelled by user")
        sys.exit(1)
    except Exception:
        logger.exception("Import operation failed")
        print("❌ Import failed: unexpected error. See logs for details.")
        sys.exit(1)
    
    finally:
        # Shutdown write queue to prevent hanging
        try:
            from serena.infrastructure.write_queue import write_queue
            shutdown_success = write_queue.shutdown(timeout=5.0)
            if shutdown_success:
                logger.debug("✅ Write queue shutdown completed")
            else:
                logger.debug("⚠️ Write queue shutdown timeout")
        except ImportError:
            # Write queue not available - normal for some configurations
            pass
        except Exception as queue_e:
            logger.debug(f"Write queue cleanup warning: {queue_e}")


def register(sub: Any) -> None:
    """Register the import command."""
    p = sub.add_parser("import", help="Bulk import archives and documents from file")
    p.add_argument("file", help="Input file (JSON, JSON Lines, or CSV format)")
    p.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    p.set_defaults(func=cmd_import)