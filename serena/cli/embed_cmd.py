"""CLI command for code embedding functionality."""

import argparse
from pathlib import Path

from serena.cli.common import setup_logging, validate_configuration
from serena.infrastructure.code_embedding import CodeEmbeddingSystem
from serena.settings import settings


def cmd_embed(args: argparse.Namespace) -> int:
    """Command handler for code embedding operations."""
    setup_logging(args.verbose)

    try:
        validate_configuration()
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return 1

    # Initialize the code embedding system
    try:
        project_root = args.project_root or str(Path.cwd())
        embedding_system = CodeEmbeddingSystem(
            project_root=project_root,
            db_path=settings.memory_db,
        )

        if args.action == "index":
            return _cmd_embed_index(embedding_system, args)
        elif args.action == "search":
            return _cmd_embed_search(embedding_system, args)
        elif args.action == "stats":
            return _cmd_embed_stats(embedding_system, args)
        else:
            print(f"❌ Unknown embed action: {args.action}")
            return 1

    except Exception as e:
        print(f"❌ Error initializing code embedding system: {e}")
        return 1


def _cmd_embed_index(system: CodeEmbeddingSystem, args: argparse.Namespace) -> int:
    """Handle code indexing command."""
    try:
        print("🚀 Starting codebase embedding...")

        if args.files:
            # Index specific files
            print(f"📁 Indexing {len(args.files)} specific files...")
            processed = 0
            errors = 0

            for filepath in args.files:
                try:
                    if system.embed_file(filepath, force_reindex=args.force):
                        processed += 1
                        print(f"✅ Embedded: {filepath}")
                    else:
                        print(f"⏭️  Skipped: {filepath} (unchanged)")
                except Exception as e:
                    print(f"❌ Failed to embed {filepath}: {e}")
                    errors += 1

            print(f"\n📊 Summary: {processed} files processed, {errors} errors")
            return 0 if errors == 0 else 1

        else:
            # Index entire codebase
            stats = system.embed_codebase(force_reindex=args.force)

            print(f"\n📊 Embedding Complete:")
            print(f"   📁 Files found: {stats['files_found']}")
            print(f"   ✅ Files processed: {stats['files_processed']}")
            print(f"   ⏭️  Files skipped: {stats['files_skipped']}")
            print(f"   🧩 Chunks created: {stats.get('chunks_created', 0)}")
            print(f"   🎯 Embeddings generated: {stats.get('embeddings_generated', 0)}")
            print(f"   ❌ Errors: {stats['errors']}")

            return 0 if stats["errors"] == 0 else 1

    except Exception as e:
        print(f"❌ Error during embedding: {e}")
        return 1


def _cmd_embed_search(system: CodeEmbeddingSystem, args: argparse.Namespace) -> int:
    """Handle code search command."""
    try:
        query = args.query
        limit = args.limit or 10

        print(f"🔍 Searching codebase for: '{query}'")
        results = system.search_code(query, limit=limit)

        if not results:
            print("No results found.")
            return 0

        print(f"\n📊 Found {len(results)} results:")
        print("-" * 80)

        for i, result in enumerate(results, 1):
            print(
                f"\n{i}. {result['filepath']}:{result['start_line']}-{result['end_line']}"
            )
            print(f"   📊 Similarity: {result['similarity']:.3f}")
            print(f"   💻 Preview: {result['preview']}")

        return 0

    except Exception as e:
        print(f"❌ Error during search: {e}")
        return 1


def _cmd_embed_stats(system: CodeEmbeddingSystem, args: argparse.Namespace) -> int:
    """Handle stats command."""
    try:
        stats = system.get_stats()

        print("📊 Code Embedding Statistics:")
        print(f"   📁 Files indexed: {stats['files_indexed']}")
        print(f"   🎯 Embeddings generated: {stats['embeddings_generated']}")
        print(f"   📈 Average chunks per file: {stats['average_chunks_per_file']:.1f}")

        return 0

    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return 1


def register(subparsers) -> None:
    """Register the embed command with the argument parser."""
    parser = subparsers.add_parser(
        "embed",
        help="Code embedding operations for semantic code search",
        description="Embed code files (*.py, *.ts, *.tsx, *.js, *.jsx) into semantic search index. "
                   "For documentation indexing, use 'serena index' instead.",
    )

    # Add verbose flag
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    # Add project root option
    parser.add_argument(
        "--project-root",
        type=str,
        help="Project root directory (default: current directory)",
    )

    # Add subcommands
    subparsers_embed = parser.add_subparsers(
        dest="action", help="Embed actions", required=True
    )

    # Index subcommand
    parser_index = subparsers_embed.add_parser(
        "index", help="Index codebase or specific files for embedding"
    )
    parser_index.add_argument(
        "--force",
        action="store_true",
        help="Force reindexing of all files (ignore SHA-256 checksums)",
    )
    parser_index.add_argument(
        "--files",
        nargs="*",
        help="Specific files to index (if not provided, indexes entire codebase)",
    )

    # Search subcommand
    parser_search = subparsers_embed.add_parser(
        "search", help="Search embedded code using semantic similarity"
    )
    parser_search.add_argument("query", type=str, help="Search query")
    parser_search.add_argument(
        "--limit", type=int, default=10, help="Maximum number of results (default: 10)"
    )

    # Stats subcommand
    subparsers_embed.add_parser("stats", help="Show embedding statistics")

    parser.set_defaults(func=cmd_embed)
