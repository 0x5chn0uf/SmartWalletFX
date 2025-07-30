# Serena CLI Commands Reference

> **Overview**: Complete reference for all Serena CLI commands and their usage patterns  
> **Audience**: Developers, Claude Code, and contributors  
> **Last Updated**: July 2025

## What is Serena CLI?

Serena provides a command-line interface for managing semantic search and memory operations in the SmartWalletFX project. All operations are performed through a local server to ensure consistency and performance.

## Command Categories

### 🚀 **Core Operations**

- [`init`](#init) - Initialize database and configuration
- [`serve`](#serve) - Start the local server
- [`index`](#index) - Index content for search
- [`search`](#search) - Semantic search across memories
- [`context`](#context) - Multi-source context retrieval

### 📋 **Memory Management**

- [`get`](#get) - Retrieve specific memory by ID
- [`latest`](#latest) - Get recently indexed memories
- [`delete`](#delete) - Remove memories from the system

### 🔧 **System Administration**

- [`maintenance`](#maintenance) - Run database maintenance
- [`pool`](#pool) - Monitor server status and health

---

## Command Details

### `init`

**Purpose**: Initialize the Serena database and configuration files.

```bash
serena init
```

**Usage**: Run once when setting up Serena in a new project. Creates the SQLite database, configuration files, and sets up the initial schema.

**Output**: Creates `.serena/` directory with database and config files.

---

### `serve`

**Purpose**: Start the local Serena server for processing requests.

```bash
serena serve [options]
```

**Arguments**:

- `--host HOST` - Server host (default: localhost)
- `--port PORT` - Server port (default: 8899)
- `--watch` - Enable auto-reload for development
- `-v, --verbose` - Enable verbose logging

**Usage**: Must be running for other commands to work. Starts FastAPI server with semantic search capabilities.

**Example**:

```bash
# Start server with default settings
serena serve

# Start with custom port and auto-reload
serena serve --port 9000 --watch
```

---

### `index`

**Purpose**: Index content files for semantic search.

```bash
serena index [path] [options]
```

**Arguments**:

- `path` - Directory or file path to index (optional, defaults to current directory)
- `--limit LIMIT` - Maximum number of files to process
- `--force` - Force re-indexing of existing content
- `-v, --verbose` - Enable verbose logging

**Usage**: Processes text files and creates vector embeddings for semantic search. Automatically detects TaskMaster directories.

**Example**:

```bash
# Index current directory
serena index

# Index specific directory with force refresh
serena index /path/to/docs --force

# Index with file limit
serena index --limit 100
```

---

### `search`

**Purpose**: Perform semantic search across indexed memories.

```bash
serena search "query" [options]
```

**Arguments**:

- `query` - Search query string (required)
- `--limit LIMIT` - Number of results to return (default: 10)
- `--format FORMAT` - Output format: `default`, `claude-optimized`, `compact`, `json`
- `--advanced` - Use advanced search mode
- `-v, --verbose` - Enable verbose logging

**Formats**:

- **`default`**: Human-readable verbose format with full details
- **`claude-optimized`**: Token-efficient format for LLM consumption (~60% reduction)
- **`compact`**: Ultra-compact single-line results (~80% reduction)
- **`json`**: Machine-readable structured data

**Usage**: Search through all indexed content using semantic similarity.

**Examples**:

```bash
# Basic search
serena search "user authentication"

# Claude Code optimized search
serena search "database patterns" --format=claude-optimized --limit=5

# Compact format for quick scanning
serena search "FastAPI endpoints" --format=compact

# JSON for programmatic use
serena search "error handling" --format=json
```

**Claude-Optimized Output Example**:

```
SEARCH: user authentication
RESULTS: 3 found | SCORES: 0.465-0.416

1. [T125] JWT Implementation Guide ✅
   🔥 0.465 | 🏷️ task | 📁 auth-guide.md
   💬 Complete JWT authentication flow with middleware...

2. [121] Auth State Management 📋
   📊 0.453 | 🏷️ reflection | 📁 reflection-121.md
   💬 React authentication state with protected routes...
```

---

### `context`

**Purpose**: Retrieve semantically-relevant context from multiple sources for Claude Code.

```bash
serena context "query" [options]
```

**Arguments**:

- `query` - Context query string (required)
- `--limit LIMIT` - Maximum results per source (default: 10)
- `--scope SCOPE` - Limit to: `all`, `tasks`, `memories`, `code`
- `--format FORMAT` - Output format: `claude-optimized`, `json`, `default`
- `-v, --verbose` - Enable verbose logging

**Sources**:

- **TaskMaster tasks**: Project task definitions and progress
- **Memory bank**: Historical context and architectural decisions
- **Semantic memories**: Serena's indexed content with relevance scoring

**Usage**: Optimized for Claude Code to gather comprehensive context efficiently.

**Examples**:

```bash
# Get context for implementation
serena context "implement rate limiting"

# Focus on tasks only
serena context "authentication flow" --scope=tasks

# JSON output for programmatic use
serena context "database migration" --format=json --limit=5
```

**Output Example**:

```
CONTEXT: implement rate limiting
RELEVANCE: 0.84 | SOURCES: 2 tasks, 3 memories, 0 code refs

TASKS:
- [T089] Rate Limiting Middleware - ✅ done
  Key: Implemented Redis-based rate limiting with configurable thresholds

MEMORIES:
- 🧠 middleware-patterns: Rate limiting strategies and implementation patterns
- 📚 redis-integration: Connection pooling and performance optimization

SUMMARY:
Context analysis complete: 2 relevant tasks found, 3 memory entries located.
```

---

### `get`

**Purpose**: Retrieve detailed information about a specific memory by ID.

```bash
serena get TASK_ID [options]
```

**Arguments**:

- `TASK_ID` - Unique identifier for the memory (required)
- `--content` - Include full file content in output
- `-v, --verbose` - Enable verbose logging

**Usage**: Get detailed information about a specific indexed item.

**Example**:

```bash
# Get basic info
serena get T125

# Get with full content
serena get T125 --content
```

---

### `latest`

**Purpose**: Show recently indexed memories.

```bash
serena latest [options]
```

**Arguments**:

- `--limit LIMIT` - Number of recent items to show (default: 10)
- `-v, --verbose` - Enable verbose logging

**Usage**: Quick overview of recently added or updated content.

**Example**:

```bash
# Show 10 most recent
serena latest

# Show 20 most recent
serena latest --limit 20
```

---

### `delete`

**Purpose**: Remove specific memories from the system.

```bash
serena delete [options]
```

**Arguments**:

- `--id ID` - Specific memory ID to delete
- `--interactive` - Interactive deletion mode
- `-v, --verbose` - Enable verbose logging

**Usage**: Clean up obsolete or incorrect memories. Use with caution.

**Example**:

```bash
# Delete specific memory
serena delete --id T125

# Interactive mode
serena delete --interactive
```

---

### `maintenance`

**Purpose**: Run database maintenance operations.

```bash
serena maintenance [options]
```

**Arguments**:

- `--force` - Force maintenance regardless of schedule
- `--vacuum` - Run database vacuum operation (reclaims disk space and optimizes performance)
- `--backup` - Create backup before maintenance
- `-v, --verbose` - Enable verbose logging

**Usage**: Optimize database performance and clean up unused space.

**Example**:

```bash
# Run scheduled maintenance
serena maintenance

# Force vacuum with backup
serena maintenance --force --vacuum --backup
```

---

### `pool`

**Purpose**: Monitor server status and health.

```bash
serena pool <subcommand> [options]
```

**Subcommands**:

- `status` - Show server connection status
- `health` - Display detailed health metrics

**Arguments**:

- `-v, --verbose` - Enable verbose logging

**Usage**: Check if the Serena server is running and healthy.

**Examples**:

```bash
# Check server status
serena pool status

# Get detailed health info
serena pool health
```

---

## Usage Patterns

### For Claude Code Integration

**Primary Commands**:

```bash
# Get comprehensive context (most common)
serena context "feature to implement" --format=claude-optimized

# Detailed semantic search when needed
serena search "specific pattern" --format=claude-optimized --limit=5

# Get specific task details
serena get T125
```

### For Development Workflow

**Setup**:

```bash
serena init
serena serve --watch  # In background
```

**Content Management**:

```bash
serena index .                    # Index current project
serena search "what I'm looking for"
serena latest                     # See recent additions
```

### For System Administration

**Maintenance**:

```bash
serena maintenance --vacuum --backup
serena pool health
```

---

## Output Formats Comparison

| Format             | Use Case         | Token Efficiency | Structure                   |
| ------------------ | ---------------- | ---------------- | --------------------------- |
| `default`          | Human reading    | Baseline         | Verbose, detailed           |
| `claude-optimized` | LLM consumption  | ~60% reduction   | Structured, token-efficient |
| `compact`          | Quick scanning   | ~80% reduction   | Single-line results         |
| `json`             | Programmatic use | Variable         | Machine-readable            |

---

## Error Handling

All commands provide structured error messages and suggested solutions:

```bash
❌ Serena server not available or search failed
   💡 Solution: Start the server with: serena serve
```

Use `--verbose` flag for detailed error information and debugging.

---

## Integration Notes

- **Server Dependency**: Most commands require `serena serve` to be running
- **TaskMaster Integration**: Automatically detects and indexes `.taskmaster/` directories
- **Memory Safety**: All operations include proper cleanup and connection management
- **Performance**: Claude-optimized formats significantly reduce token usage for LLM workflows
