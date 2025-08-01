"""FastAPI server for Serena memory bridge API."""

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from serena.core.errors import (
    ErrorCode,
    SerenaException,
    create_error_response,
    create_success_response,
)
from serena.core.models import (
    Archive,
    Embedding,
    SearchResult,
    compute_content_hash,
    generate_summary,
)
from serena.database.session import get_db_session
from serena.infrastructure.embeddings import (
    chunk_content,
    get_default_generator,
    preprocess_content,
)
from serena.infrastructure.write_queue import WriteOperationType, write_queue
from serena.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    import logging
    import time

    from serena.infrastructure.embeddings import get_default_generator
    from serena.scripts.maintenance import MaintenanceService

    # use consolidated settings object
    # from serena import config (removed)
    # Use both print and logging to ensure visibility
    startup_start = time.time()
    print("🚀 Serena server startup beginning...")
    print("📋 Configuration check:")
    print(f"   - Database path: {settings.memory_db}")

    # Embeddings are always required; load model synchronously
    print("🤖 Initializing embedding model...")
    model_start = time.time()
    try:
        generator = get_default_generator()
        print(f"   - Model name: {generator.model_name}")
        print(f"   - Expected dimension: {generator.embedding_dim}")

        # Force synchronous model loading
        print("   - Loading model weights...")
        success = generator.load_model_now()
        model_time = time.time() - model_start

        if not success:
            # Embeddings were expected but model could not be loaded → abort.
            print(
                f"❌ Failed to load embedding model after {model_time:.2f}s – aborting startup"
            )
            raise RuntimeError("Embedding model failed to load; startup aborted")

        print(f"✅ Embedding model loaded successfully in {model_time:.2f}s")
        print(f"   - Model: {generator.model_name}")
        print(f"   - Dimension: {generator.embedding_dim}")
        print("   - Status: Ready for semantic search")
    except Exception as exc:
        model_time = time.time() - model_start
        print(f"❌ Failed to preload embedding model after {model_time:.2f}s: {exc}")
        print("   - Status: Embedding search will be UNAVAILABLE")

    # Initialize write queue for server operations
    print("🔄 Initializing write queue...")
    queue_start = time.time()
    try:
        from serena.infrastructure.write_queue import write_queue, _create_write_queue
        import serena.infrastructure.write_queue as wq_module

        # Initialize global write queue if not already done
        if wq_module.write_queue is None:
            wq_module.write_queue = _create_write_queue()

        queue_time = time.time() - queue_start
        print(f"✅ Write queue initialized successfully in {queue_time:.2f}s")
        print(f"   - Queue size limit: {wq_module.write_queue.max_queue_size}")
        print(f"   - Workers: {wq_module.write_queue.worker_count}")
        print("   - Status: Ready for async operations")
    except Exception as exc:
        queue_time = time.time() - queue_start
        print(f"❌ Failed to initialize write queue after {queue_time:.2f}s: {exc}")
        print("   - Status: Async operations will be UNAVAILABLE")

    # Start maintenance service
    maintenance_service = MaintenanceService()
    maintenance_service.start_background_service()
    app.state.maintenance_service = maintenance_service

    startup_time = time.time() - startup_start
    print(f"🎉 Serena server startup completed in {startup_time:.2f}s")

    yield

    # Graceful shutdown with proper timeout handling
    import signal
    import asyncio

    shutdown_start = time.time()
    print("🛑 Serena server shutting down gracefully...")

    # Shutdown maintenance service
    if hasattr(app.state, "maintenance_service") and app.state.maintenance_service:
        print("   - Stopping maintenance service...")
        try:
            app.state.maintenance_service.stop()
            print("   ✅ Maintenance service stopped")
        except Exception as exc:
            print(f"   ⚠️ Maintenance service shutdown error: {exc}")

    # Shutdown write queue gracefully with better error handling
    print("   - Shutting down write queue...")
    try:
        from serena.infrastructure.write_queue import write_queue

        # Get current queue status before shutdown
        metrics = write_queue.get_metrics()
        pending_ops = metrics.current_queue_size

        if pending_ops > 0:
            print(f"   - Waiting for {pending_ops} pending operations...")

        # Attempt graceful shutdown with timeout
        shutdown_timeout = min(30.0, max(10.0, pending_ops * 0.5))  # Dynamic timeout
        shutdown_success = write_queue.shutdown(timeout=shutdown_timeout)

        if shutdown_success:
            print("   ✅ Write queue shutdown completed")
        else:
            print(f"   ⚠️ Write queue shutdown timeout after {shutdown_timeout}s")

            # Get final metrics to see what was lost
            final_metrics = write_queue.get_metrics()
            if final_metrics.current_queue_size > 0:
                print(
                    f"   ⚠️ {final_metrics.current_queue_size} operations may have been lost"
                )

    except Exception as exc:
        print(f"   ❌ Write queue shutdown error: {exc}")

    # Close database connections
    print("   - Closing database connections...")
    try:
        from serena.database.session import get_db_manager

        db_manager = get_db_manager()
        db_manager.close()
        print("   ✅ Database connections closed")
    except Exception as exc:
        print(f"   ⚠️ Database cleanup error: {exc}")

    # Final cleanup
    shutdown_time = time.time() - shutdown_start
    print(f"✅ Serena server shutdown completed in {shutdown_time:.2f}s")


async def _upsert_archive_direct(
    db: Session,
    task_id: str,
    markdown_text: str,
    filepath: Optional[str] = None,
    title: Optional[str] = None,
    kind: Optional["TaskKind"] = None,
    status: Optional["TaskStatus"] = None,
    completed_at: Optional[datetime] = None,
    async_write: bool = True,
) -> bool:
    """Direct archive upsert without using Memory class."""

    def _upsert_internal():
        # Create a new database session for thread safety
        from serena.infrastructure.database import get_session

        # Pre-process & chunk content for embeddings
        clean_content = preprocess_content(markdown_text)
        chunks = chunk_content(clean_content)

        # Extract title if not provided - use local variable
        extracted_title = title
        if not extracted_title:
            for line in markdown_text.splitlines():
                if line.startswith("#"):
                    extracted_title = line.lstrip("# ").strip()
                    break

        try:
            # Use a fresh session for thread safety
            with get_session() as session:
                # Upsert main archive row with row-level locking
                archive = (
                    session.query(Archive)
                    .filter_by(task_id=task_id)
                    .with_for_update()
                    .first()
                )

                if archive:
                    # Update existing archive
                    archive.title = extracted_title or f"Archive {task_id}"
                    archive.filepath = filepath or f"archive-{task_id}.md"
                    archive.sha256 = compute_content_hash(markdown_text)
                    archive.kind = kind.value if kind else "archive"
                    archive.status = status.value if status else None
                    archive.completed_at = completed_at
                    archive.summary = generate_summary(markdown_text)
                    archive.updated_at = datetime.now()
                else:
                    # Create new archive
                    archive = Archive(
                        task_id=task_id,
                        title=extracted_title or f"Archive {task_id}",
                        filepath=filepath or f"archive-{task_id}.md",
                        sha256=compute_content_hash(markdown_text),
                        kind=kind.value if kind else "archive",
                        status=status.value if status else None,
                        completed_at=completed_at,
                        summary=generate_summary(markdown_text),
                    )
                    session.add(archive)

                # Delete existing embeddings for this task
                session.query(Embedding).filter_by(task_id=task_id).delete()

                # Capture archive values while session is still active to avoid detached instance errors
                archive_task_id = archive.task_id
                archive_title = archive.title
                archive_summary = archive.summary or ""

                # Update FTS search index
                try:
                    from sqlalchemy import text

                    # Delete existing FTS entry
                    session.execute(
                        text("DELETE FROM archives_fts WHERE task_id = :task_id"),
                        {"task_id": task_id},
                    )
                    # Insert updated FTS entry
                    session.execute(
                        text(
                            "INSERT INTO archives_fts (task_id, title, summary) VALUES (:task_id, :title, :summary)"
                        ),
                        {
                            "task_id": archive_task_id,
                            "title": archive_title,
                            "summary": archive_summary,
                        },
                    )
                except Exception as fts_exc:
                    # FTS index update is not critical
                    print(
                        f"❌ Failed to update FTS index for task {task_id}: {fts_exc}"
                    )

                # Commit the transaction
                session.commit()

            # Queue embeddings for async generation (non-blocking) - moved after session commit
            from serena.infrastructure.embeddings import get_embedding_queue

            if chunks:
                embedding_queue = get_embedding_queue()
                embedding_queued = embedding_queue.submit_embedding_request(
                    task_id=task_id,
                    content_chunks=chunks,
                    priority=1,  # Standard priority for archive operations
                )

                if embedding_queued:
                    print(f"Queued embeddings for task {task_id}")
                else:
                    print(
                        f"Failed to queue embeddings for task {task_id}, search will be unavailable until embeddings are generated"
                    )

            return True

        except Exception as exc:
            print(f"❌ Database error during upsert for {task_id}: {exc}")
            return False

    if async_write:
        try:
            from serena.infrastructure.write_queue import write_queue as wq

            if wq is None:
                print(
                    f"Write queue not available for task {task_id}, falling back to sync"
                )
                return _upsert_internal()

            operation_id = wq.submit(
                _upsert_internal,
                priority=1,
                operation_type=WriteOperationType.UPSERT,
            )
            print(
                f"Queued async upsert for task {task_id} with operation ID {operation_id}"
            )
            return True
        except Exception as exc:
            print(f"Failed to queue async upsert for task {task_id}: {exc}")
            # Fall back to synchronous processing
            return _upsert_internal()
    else:
        return _upsert_internal()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Serena Memory Bridge API",
        description="API for accessing and managing task memory archives with semantic search",
        version="0.1.0",
        lifespan=lifespan,
        # Production optimizations
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )

    # Configure CORS with environment-specific settings
    if not settings.is_production or settings.cors_origins != "":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=(
                settings.cors_origins_list
                if not settings.is_production
                else ["https://yourdomain.com"]
            ),
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_methods_list,
            allow_headers=[settings.cors_allow_headers],
        )

    # Add security headers for production
    if settings.is_production:

        @app.middleware("http")
        async def add_security_headers(request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
            return response

    # Enhanced error handling middleware with monitoring
    @app.middleware("http")
    async def error_middleware(request: Request, call_next):
        import traceback

        try:
            response = await call_next(request)
            return response
        except SerenaException as e:
            # Handle Serena-specific exceptions
            print(
                "Serena exception in %s %s: %s",
                request.method,
                request.url.path,
                e.message,
            )
            error_response = e.to_dict()
            return JSONResponse(status_code=500, content=error_response)
        except HTTPException as e:
            # Convert FastAPI HTTPExceptions to structured format
            if e.status_code >= 500:
                print(
                    "HTTP exception in %s %s: %s",
                    request.method,
                    request.url.path,
                    e.detail,
                )
            else:
                print(
                    "HTTP exception in %s %s: %s",
                    request.method,
                    request.url.path,
                    e.detail,
                )

            error_response = create_error_response(
                code=ErrorCode.INTERNAL_ERROR, message=e.detail
            )
            return JSONResponse(status_code=e.status_code, content=error_response)
        except Exception as e:
            # Handle unexpected exceptions with full logging
            error_id = str(uuid.uuid4())[:8]
            print(
                f"Unexpected error [{error_id}] in {request.method} {request.url.path}: {str(e)}\n{traceback.format_exc() if settings.log_level.upper() == 'DEBUG' else ''}",
            )

            error_response = create_error_response(
                code=ErrorCode.INTERNAL_ERROR,
                message=(
                    "An unexpected error occurred" if settings.is_production else str(e)
                ),
                details={
                    "error_id": error_id,
                    "traceback": (
                        traceback.format_exc() if not settings.is_production else None
                    ),
                },
            )
            return JSONResponse(status_code=500, content=error_response)

    # Add timing middleware
    @app.middleware("http")
    async def add_timing_header(request, call_next):
        import time

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Add execution time to response headers
        response.headers["X-Process-Time"] = str(round(process_time, 4))

        # Log execution time for API endpoints (skip probe endpoints)
        if request.url.path not in [
            "/",
            "/health",
            "/ready",
            "/live",
        ]:  # Skip root and health check
            # Build full URL with query parameters
            url_with_query = str(request.url.path)
            if request.url.query:
                url_with_query += "?" + request.url.query

            # Use print for immediate visibility
            print(
                f"{request.method} {url_with_query} - {process_time:.5f}s - {response.status_code}"
            )

        return response

    # Dependency for database session
    def get_db():
        with get_db_session() as session:
            yield session

    @app.get("/")
    async def root():
        """Root endpoint."""
        print("🚀 Serena Memory Bridge API v0.1.0")
        return create_success_response(
            data={"message": "Serena Memory Bridge API", "version": "0.1.0"}
        )

    @app.get("/health")
    async def health_check():
        """Enhanced health check endpoint with comprehensive system monitoring."""
        from serena.infrastructure.health import get_health_manager

        health_manager = get_health_manager()
        health_data = health_manager.get_comprehensive_health()

        # Print health status to console instead of returning JSON
        print(f"🏥 Health Check: {health_data['status']}")

        if health_data["status"] == "unhealthy":
            print("❌ Server is unhealthy")
            print(f"   Details: {health_data}")
            return JSONResponse(
                status_code=503,
                content=create_error_response(
                    code=ErrorCode.SERVER_UNAVAILABLE,
                    message="Server is unhealthy",
                    details=health_data,
                ),
            )
        else:
            print("✅ Server is healthy")
            print(
                f"   Database: {health_data.get('database', {}).get('status', 'unknown')}"
            )
            print(
                f"   Archive count: {health_data.get('database', {}).get('archive_count', 0)}"
            )

        return create_success_response(data=health_data)

    @app.get("/ready")
    async def readiness_check():
        """Kubernetes-style readiness probe - is the service ready to serve traffic?"""
        from serena.infrastructure.health import get_health_manager

        health_manager = get_health_manager()
        readiness_data = health_manager.get_readiness_check()

        # Print readiness status to console
        print(
            f"🔄 Readiness Check: {'Ready' if readiness_data['ready'] else 'Not Ready'}"
        )

        if readiness_data["ready"]:
            print("✅ Service is ready to serve traffic")
            return create_success_response(data=readiness_data)
        else:
            print("❌ Service not ready")
            print(f"   Details: {readiness_data}")
            return JSONResponse(
                status_code=503,
                content=create_error_response(
                    code=ErrorCode.SERVER_UNAVAILABLE,
                    message="Service not ready",
                    details=readiness_data,
                ),
            )

    @app.get("/live")
    async def liveness_check():
        """Kubernetes-style liveness probe - is the service alive?"""
        from serena.infrastructure.health import get_health_manager

        health_manager = get_health_manager()
        liveness_data = health_manager.get_liveness_check()

        # Print liveness status to console
        print(
            f"💓 Liveness Check: {'Alive' if liveness_data.get('alive', False) else 'Dead'}"
        )

        return create_success_response(data=liveness_data)

    @app.get("/maintenance/status")
    async def get_maintenance_status(request: "Request"):
        """Get the status of the maintenance service."""
        service = request.app.state.maintenance_service
        if not service:
            return create_error_response(
                code=ErrorCode.SERVER_UNAVAILABLE,
                message="Maintenance service not running",
            )
        status_data = service.get_status()
        print(f"🔧 Maintenance Service Status: {status_data.get('status', 'unknown')}")
        return create_success_response(data=status_data)

    @app.post("/maintenance/run/{operation}")
    async def run_maintenance_operation(operation: str, request: "Request"):
        """Trigger a specific maintenance operation."""
        service = request.app.state.maintenance_service
        if not service:
            return create_error_response(
                code=ErrorCode.SERVER_UNAVAILABLE,
                message="Maintenance service not running",
            )
        try:
            service.run_operation(operation)
            print(f"✅ Maintenance operation '{operation}' triggered successfully")
            return create_success_response(
                data={"message": f"Operation '{operation}' triggered successfully"}
            )
        except ValueError:
            return create_error_response(
                code=ErrorCode.INVALID_INPUT,
                message=f"Invalid operation: {operation}",
                details={"operation": operation},
            )
        except Exception as e:
            return create_error_response(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Operation failed: {str(e)}",
                details={"operation": operation, "error": str(e)},
            )

    @app.get("/archives")
    async def list_archives(
        limit: int = 20, offset: int = 0, db: Session = Depends(get_db)
    ):
        """List archived tasks."""
        try:
            # Validate parameters
            if limit < 1 or limit > 100:
                return create_error_response(
                    code=ErrorCode.INVALID_INPUT,
                    message="Limit must be between 1 and 100",
                    details={"limit": limit},
                )

            if offset < 0:
                return create_error_response(
                    code=ErrorCode.INVALID_INPUT,
                    message="Offset must be non-negative",
                    details={"offset": offset},
                )

            # Sort by latest completion date, with fallback to updated_at for NULL completed_at
            archives = (
                db.query(Archive)
                .order_by(
                    Archive.completed_at.desc().nulls_last(), Archive.updated_at.desc()
                )
                .offset(offset)
                .limit(limit)
                .all()
            )

            total_count = db.query(Archive).count()

            data = {
                "archives": [
                    {
                        "task_id": archive.task_id,
                        "title": archive.title,
                        "kind": archive.kind,
                        "status": archive.status,
                        "completed_at": (
                            archive.completed_at.isoformat()
                            if archive.completed_at
                            else None
                        ),
                        "summary": archive.summary,
                        "created_at": archive.created_at.isoformat(),
                        "updated_at": archive.updated_at.isoformat(),
                        "filepath": archive.filepath,
                    }
                    for archive in archives
                ],
                "total": total_count,
                "limit": limit,
                "offset": offset,
            }

            print(
                f"📁 Retrieved {len(data['archives'])} archives (total: {data['total']})"
            )
            return create_success_response(data=data)
        except Exception as e:
            return create_error_response(
                code=ErrorCode.DATABASE_QUERY_FAILED,
                message="Failed to retrieve archives",
                details={"error": str(e)},
            )

    @app.get("/archives/{task_id}")
    async def get_archive(task_id: str, db: Session = Depends(get_db)):
        """Get specific archive by task ID."""
        try:
            # Validate task_id
            if not task_id or len(task_id.strip()) == 0:
                return create_error_response(
                    code=ErrorCode.INVALID_TASK_ID,
                    message="Task ID cannot be empty",
                    details={"task_id": task_id},
                )

            archive = db.query(Archive).filter(Archive.task_id == task_id).first()

            if not archive:
                return create_error_response(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message=f"Archive not found: {task_id}",
                    details={"task_id": task_id},
                )

            data = {
                "task_id": archive.task_id,
                "title": archive.title,
                "filepath": archive.filepath,
                "sha256": archive.sha256,
                "kind": archive.kind,
                "status": archive.status,
                "completed_at": (
                    archive.completed_at.isoformat() if archive.completed_at else None
                ),
                "summary": archive.summary,
                "created_at": archive.created_at.isoformat(),
                "updated_at": archive.updated_at.isoformat(),
                "embedding_version": archive.embedding_version,
                "last_embedded_at": (
                    archive.last_embedded_at.isoformat()
                    if archive.last_embedded_at
                    else None
                ),
            }

            print(f"📄 Retrieved archive: {archive.task_id} - {archive.title}")
            return create_success_response(data=data)
        except Exception as e:
            return create_error_response(
                code=ErrorCode.DATABASE_QUERY_FAILED,
                message="Failed to retrieve archive",
                details={"task_id": task_id, "error": str(e)},
            )

    @app.delete("/archives/{task_id}")
    async def delete_archive(task_id: str, db: Session = Depends(get_db)):
        """Delete archive by task ID."""
        try:
            # Validate task_id
            if not task_id or len(task_id.strip()) == 0:
                return create_error_response(
                    code=ErrorCode.INVALID_TASK_ID,
                    message="Task ID cannot be empty",
                    details={"task_id": task_id},
                )

            archive = db.query(Archive).filter(Archive.task_id == task_id).first()

            if not archive:
                return create_error_response(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message=f"Archive not found: {task_id}",
                    details={"task_id": task_id},
                )

            # Store title before deletion
            title = archive.title

            # Delete the archive (embeddings will be cascade deleted)
            db.delete(archive)
            db.commit()

            print(f"🗑️ Archive {task_id} deleted successfully: {title}")
            return create_success_response(
                data={
                    "message": f"Archive {task_id} deleted successfully",
                    "task_id": task_id,
                    "title": title,
                }
            )
        except Exception as e:
            db.rollback()
            return create_error_response(
                code=ErrorCode.DATABASE_TRANSACTION_FAILED,
                message="Failed to delete archive",
                details={"task_id": task_id, "error": str(e)},
            )

    @app.get("/search")
    async def search_archives(
        q: str, limit: int = 10, threshold: float = 0.1, db: Session = Depends(get_db)
    ):
        """Search archives using semantic similarity."""
        try:
            # Validate parameters
            if not q or len(q.strip()) == 0:
                return create_error_response(
                    code=ErrorCode.INVALID_INPUT,
                    message="Search query cannot be empty",
                    details={"query": q},
                )

            if limit < 1 or limit > 100:
                return create_error_response(
                    code=ErrorCode.INVALID_INPUT,
                    message="Limit must be between 1 and 100",
                    details={"limit": limit},
                )

            if threshold < 0 or threshold > 1:
                return create_error_response(
                    code=ErrorCode.INVALID_INPUT,
                    message="Threshold must be between 0 and 1",
                    details={"threshold": threshold},
                )

            from serena.infrastructure.search import SearchEngine

            search_engine = SearchEngine()
            search_results = search_engine.search(query=q, k=limit)

            results = [
                {
                    "task_id": result.task_id,
                    "title": result.title,
                    "score": result.score or 0.0,
                    "excerpt": result.excerpt or "",
                    "kind": result.kind.value if result.kind else None,
                    "status": result.status.value if result.status else None,
                    "completed_at": (
                        result.completed_at.isoformat() if result.completed_at else None
                    ),
                    "filepath": result.filepath,
                }
                for result in search_results
                if result.score is None or result.score >= threshold
            ]

            data = {
                "query": q,
                "results": results,
                "total": len(results),
                "threshold": threshold,
            }

            print(f"🔍 Search completed: {len(results)} results for '{q}'")
            return create_success_response(data=data)

        except RuntimeError as exc:
            # Handle embedding-related runtime errors specifically
            if "embedding" in str(exc).lower():
                return create_error_response(
                    code=ErrorCode.EMBEDDING_SERVICE_ERROR,
                    message="Semantic search unavailable - embeddings required",
                    details={
                        "error": str(exc),
                        "solution": "Ensure embedding model is loaded and content is indexed with embeddings",
                    },
                )
            else:
                return create_error_response(
                    code=ErrorCode.SEARCH_QUERY_FAILED,
                    message="Search operation failed",
                    details={"error": str(exc)},
                )
        except Exception as exc:
            return create_error_response(
                code=ErrorCode.SEARCH_QUERY_FAILED,
                message="Search operation failed",
                details={"query": q, "error": str(exc)},
            )

    @app.get("/stats")
    async def get_statistics(db: Session = Depends(get_db)):
        """Get database statistics."""
        try:
            archive_count = db.query(Archive).count()
            embedding_count = db.query(Embedding).count()

            # Get count by kind
            kind_counts = {}
            for kind in ["archive", "reflection", "doc", "rule", "code"]:
                count = db.query(Archive).filter(Archive.kind == kind).count()
                if count > 0:
                    kind_counts[kind] = count

            # Get count by status
            status_counts = {}
            statuses = db.query(Archive.status).distinct().all()
            for (status,) in statuses:
                if status:
                    count = db.query(Archive).filter(Archive.status == status).count()
                    status_counts[status] = count

            data = {
                "total_archives": archive_count,
                "total_embeddings": embedding_count,
                "by_kind": kind_counts,
                "by_status": status_counts,
            }

            print(
                f"📊 Statistics: {archive_count} archives, {embedding_count} embeddings"
            )
            return create_success_response(data=data)
        except Exception as e:
            return create_error_response(
                code=ErrorCode.DATABASE_QUERY_FAILED,
                message="Failed to retrieve statistics",
                details={"error": str(e)},
            )

    @app.get("/queue/status")
    async def get_queue_status():
        """Get write queue status and metrics."""
        try:
            from serena.infrastructure.write_queue import write_queue

            if write_queue is None:
                return create_error_response(
                    code=ErrorCode.DEPENDENCY_ERROR,
                    message="Write queue not initialized",
                    details={"component": "write_queue"},
                )

            metrics = write_queue.get_metrics()
            health = write_queue.health_check()

            data = {
                "status": health["status"],
                "health_score": health["health_score"],
                "current_queue_size": metrics.current_queue_size,
                "total_operations": metrics.total_operations,
                "successful_operations": metrics.successful_operations,
                "failed_operations": metrics.failed_operations,
                "avg_processing_time_ms": metrics.avg_processing_time_ms,
                "worker_count": health["metrics"]["worker_count"],
                "issues": health["issues"],
            }

            print(
                f"⚡ Queue status: {data['status']} - {data['current_queue_size']} items queued"
            )
            return create_success_response(data=data)
        except Exception as e:
            return create_error_response(
                code=ErrorCode.DEPENDENCY_ERROR,
                message="Failed to retrieve queue status",
                details={"error": str(e)},
            )

    @app.post("/archives")
    async def upsert_archive(
        request: dict,
        async_write: bool = None,  # Optional query parameter
        db: Session = Depends(get_db),
    ):
        """Upsert (insert or update) an archive using the server's embedding model."""
        try:
            from datetime import datetime

            from serena.cli.common import RemoteMemory
            from serena.core.models import TaskKind, TaskStatus

            # Extract data from request
            task_id = request.get("task_id")
            markdown_text = request.get("markdown_text")
            filepath = request.get("filepath")
            title = request.get("title")
            kind = request.get("kind", "archive")
            status = request.get("status")
            completed_at = request.get("completed_at")

            # Handle async_write configuration - priority order:
            # 1. Request body parameter (for explicit control)
            # 2. Query parameter (for URL-based control)
            # 3. Server configuration default
            request_async_write = request.get("async_write")
            if request_async_write is not None:
                use_async_write = bool(request_async_write)
            elif async_write is not None:
                use_async_write = async_write
            else:
                use_async_write = settings.async_write

            # Validate required fields
            if not task_id:
                return create_error_response(
                    code=ErrorCode.MISSING_REQUIRED_FIELD,
                    message="task_id is required",
                    details={"missing_field": "task_id"},
                )

            if not markdown_text:
                return create_error_response(
                    code=ErrorCode.MISSING_REQUIRED_FIELD,
                    message="markdown_text is required",
                    details={"missing_field": "markdown_text"},
                )

            # Validate task_id format
            if len(task_id) > 255:
                return create_error_response(
                    code=ErrorCode.INVALID_TASK_ID,
                    message="Task ID must be 255 characters or less",
                    details={"task_id": task_id, "length": len(task_id)},
                )

            # Validate content size
            if len(markdown_text) > 10 * 1024 * 1024:  # 10MB limit
                return create_error_response(
                    code=ErrorCode.CONTENT_TOO_LARGE,
                    message="Content exceeds maximum size limit (10MB)",
                    details={"content_size": len(markdown_text)},
                )

            # Parse completed_at if provided
            parsed_completed_at = None
            if completed_at:
                try:
                    parsed_completed_at = datetime.fromisoformat(
                        completed_at.replace("Z", "+00:00")
                    )
                except Exception:
                    return create_error_response(
                        code=ErrorCode.INVALID_INPUT,
                        message="Invalid completed_at format. Use ISO format.",
                        details={"completed_at": completed_at},
                    )

            # Parse enum values
            task_kind = None
            if kind:
                try:
                    task_kind = TaskKind(kind)
                except ValueError:
                    return create_error_response(
                        code=ErrorCode.INVALID_INPUT,
                        message=f"Invalid kind value: {kind}",
                        details={
                            "kind": kind,
                            "valid_values": [k.value for k in TaskKind],
                        },
                    )

            task_status = None
            if status:
                try:
                    task_status = TaskStatus(status)
                except ValueError:
                    return create_error_response(
                        code=ErrorCode.INVALID_INPUT,
                        message=f"Invalid status value: {status}",
                        details={
                            "status": status,
                            "valid_values": [s.value for s in TaskStatus],
                        },
                    )

            print(f"Upserting {task_id} with async_write={use_async_write}")

            # Perform upsert directly using database and write queue
            success = await _upsert_archive_direct(
                db=db,
                task_id=task_id,
                markdown_text=markdown_text,
                filepath=filepath,
                title=title,
                kind=task_kind,
                status=task_status,
                completed_at=parsed_completed_at,
                async_write=use_async_write,
            )

            if success:
                print(
                    f"📝 Archive {task_id} upserted successfully (async: {use_async_write})"
                )
                return create_success_response(
                    data={
                        "task_id": task_id,
                        "message": "Archive upserted successfully",
                        "async_write": use_async_write,
                        "processing": "queued" if use_async_write else "completed",
                    }
                )
            else:
                return create_error_response(
                    code=ErrorCode.INDEXING_FAILED,
                    message="Failed to upsert archive",
                    details={"task_id": task_id},
                )

        except Exception as exc:
            print(f"Error upserting archive {task_id}: {exc}")
            return create_error_response(
                code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error during archive upsert",
                details={"task_id": task_id, "error": str(exc)},
            )

    @app.post("/generate-embeddings")
    async def generate_embeddings(texts: list[str], db: Session = Depends(get_db)):
        """Generate embeddings using the server's pre-loaded model."""
        try:
            from serena.infrastructure.embeddings import get_default_generator

            # Validate input
            if not texts:
                return create_error_response(
                    code=ErrorCode.MISSING_REQUIRED_FIELD,
                    message="texts list is required",
                    details={"missing_field": "texts"},
                )

            if len(texts) > 100:
                return create_error_response(
                    code=ErrorCode.INVALID_INPUT,
                    message="Cannot process more than 100 texts at once",
                    details={"count": len(texts), "max_allowed": 100},
                )

            # Validate each text
            for i, text in enumerate(texts):
                if not isinstance(text, str):
                    return create_error_response(
                        code=ErrorCode.INVALID_INPUT,
                        message=f"Text at index {i} must be a string",
                        details={"index": i, "type": type(text).__name__},
                    )

                if len(text) > 8192:  # Model context limit
                    return create_error_response(
                        code=ErrorCode.CONTENT_TOO_LARGE,
                        message=f"Text at index {i} exceeds maximum length (8192 characters)",
                        details={"index": i, "length": len(text)},
                    )

            generator = get_default_generator()
            if generator.model is None:
                return create_error_response(
                    code=ErrorCode.EMBEDDING_SERVICE_UNAVAILABLE,
                    message="Embedding model not available",
                )

            embeddings = generator.generate_embeddings_batch(texts)

            print(
                f"🔢 Generated {len(embeddings)} embeddings using {generator.model_name}"
            )
            return create_success_response(
                data={
                    "embeddings": embeddings,
                    "model": generator.model_name,
                    "count": len(embeddings),
                }
            )
        except Exception as exc:
            print(f"Error generating embeddings: {exc}")
            return create_error_response(
                code=ErrorCode.EMBEDDING_GENERATION_FAILED,
                message="Failed to generate embeddings",
                details={"error": str(exc)},
            )

    @app.get("/settings", tags=["meta"])
    async def get_settings():
        """Return the effective Serena configuration for operators."""
        try:
            # Filter sensitive information in production
            settings_dict = settings.dict()
            if settings.is_production:
                # Remove potentially sensitive paths and URLs in production
                settings_dict.pop("memory_db", None)
                settings_dict.pop("log_file", None)

            print(f"⚙️ Settings retrieved (production: {settings.is_production})")
            return create_success_response(data=settings_dict)
        except Exception as e:
            return create_error_response(
                code=ErrorCode.CONFIGURATION_ERROR,
                message="Failed to retrieve settings",
                details={"error": str(e)},
            )

    return app
