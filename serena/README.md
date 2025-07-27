# Serena Memory Bridge

Serena is a lightweight knowledge base that plugs into any project, providing:

* 💡 **Semantic search** over markdown archives, reflections, and documentation.
* 📨 **Upsert API** so your tools can push fresh context at run-time.
* 🏷 **Task-aware schema** optimised for Taskmaster but generic enough for other systems.
* 🛠 **Zero-config CLI** (`serena` / `selena`) for quick indexing, search, and a tiny HTTP server.
* ⚡️ **SQLite + vector-search** backend – no external services required.

## Installation

```bash
pip install -e .  # from repo root (editable)
# or once published
pip install serena
```

## Quick start

```bash
# index your Taskmaster archives & start searching
serena init            # one-time setup (creates local DB)
serena index           # scan .taskmaster directories & upsert memories
serena search "jwt rotation" -k 5

# run lightweight server
serena serve --watch   # exposes API on http://localhost:8765

# same entry-point is also available as `selena`
selena search "embeddings schema"
```

## CLI reference
Run `serena --help` for a full list of commands or see `serena/cli.py` for implementation details.

## Embedding model
Sentence-Transformers is pulled in as an optional dependency.  The first call will download the default MiniLM-L6 model (~80 MB).  Override via `SERENA_MODEL` environment variable if you need a different encoder.

## License
MIT © SmartWalletFX Team