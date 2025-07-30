# Serena Memory Bridge

Serena is a lightweight knowledge base that plugs into any project, providing:

* 💡 **Semantic search** over markdown archives, reflections, and documentation
* 📨 **REST API** for runtime content ingestion and retrieval
* 🏷 **Task-aware schema** with support for archives, reflections, docs, rules, and code
* 🛠 **Zero-config CLI** (`serena` / `selena`) for indexing, search, and HTTP server
* ⚡️ **SQLite + vector embeddings** backend – no external services required
* 🔍 **Content deduplication** and automatic metadata extraction
* 📊 **Health monitoring** and database diagnostics

## Installation

```bash
pip install -e .  # from repo root (editable)
# or once published
pip install serena
```

## Quick Start

```bash
# One-time setup
serena init                     # creates local SQLite database

# Index content (auto-detects .taskmaster directories)
serena index                    # scan and index memories
serena index --force            # force reindex all content
serena index --directories ./docs,./archives --workers 8

# Search indexed content
serena search "jwt rotation"    # semantic search
serena search "embeddings schema" --limit 20

# Run API server
serena serve                    # start server on localhost:8765
serena serve --host 0.0.0.0 --port 9000 --watch

# Alternative entry point
selena search "authentication patterns"
```

## CLI Reference

### Core Commands

#### `serena init`
Initialize Serena database and configuration.
- `-v, --verbose`: Enable verbose logging

#### `serena index [options]`
Scan directories and index memories with semantic embeddings.
- `--directories <paths>`: Comma-separated directories to scan
- `--force`: Force reindex of existing memories  
- `--workers <int>`: Number of parallel workers (default: 4)
- `-v, --verbose`: Enable verbose logging

#### `serena search <query> [options]`
Perform semantic search across indexed memories.
- `--limit <int>`: Maximum number of results (default: 10)
- `--advanced`: Advanced search mode (planned feature)
- `-v, --verbose`: Enable verbose logging

#### `serena serve [options]`
Run HTTP API server with automatic documentation.
- `--host <address>`: Server host (default: 127.0.0.1)
- `--port <int>`: Server port (default: 8765)  
- `--watch`: Watch for file changes (planned feature)
- `-v, --verbose`: Enable verbose logging

#### `serena delete <task_id> [options]`
Delete indexed entries manually by task ID.
- `--list`: List available entries with their task IDs
- `--limit <int>`: Number of entries to show when listing (default: 20)
- `--show-remaining`: Show remaining entries after deletion
- `-v, --verbose`: Enable verbose logging

#### `serena get <task_id> [options]`
Get specific archive by task ID.
- `-v, --verbose`: Enable verbose logging

#### `serena latest [options]`
Show latest archived entries.
- `--limit <int>`: Number of entries to show (default: 10)
- `-v, --verbose`: Enable verbose logging

### Content Types

Serena automatically categorizes content by type:
- **ARCHIVE**: Completed task archives and historical records
- **REFLECTION**: Post-completion reflections and lessons learned
- **DOC**: General documentation and guides
- **RULE**: Configuration rules and patterns
- **CODE**: Code snippets and technical references

### Advanced Features

- **Automatic task ID extraction** from file paths
- **Content deduplication** using SHA-256 hashing
- **Chunked embeddings** for large documents
- **Versioned embeddings** for model upgrades
- **Health monitoring** with database metrics

## Embedding model
Sentence-Transformers is pulled in as an optional dependency.  The first call will download the default MiniLM-L6 model (~80 MB).  Override via `SERENA_MODEL` environment variable if you need a different encoder.

## License
MIT © SmartWalletFX Team