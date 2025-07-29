"""FastAPI server for Serena memory bridge API."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any
import os

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from serena.database.session import get_db_session
from serena.core.models import Archive, Embedding, SearchResult, compute_content_hash, generate_summary
from serena.core.errors import (
    ErrorCode, SerenaException,
    create_error_response, create_success_response
)
from serena.settings import settings
from serena.infrastructure.embeddings import get_default_generator, preprocess_content, chunk_content
from serena.infrastructure.write_queue import write_queue, WriteOperationType
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import uuid


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
    print("🚀 Serena server startup beginning...")
    
    logger = logging.getLogger("serena.server")
    logger.setLevel(logging.INFO)
    startup_start = time.time()
    
    print("📋 Configuration check:")
    print(f"   - Database path: {settings.memory_db}")
    
    logger.info("🚀 Serena server startup beginning...")
    logger.info("📋 Configuration check:")
    logger.info("   - Database path: %s", settings.memory_db)
    
    # Embeddings are always required; load model synchronously
    print("🤖 Initializing embedding model...")
    logger.info("🤖 Initializing embedding model...")
    model_start = time.time()
    try:
        generator = get_default_generator()
        print(f"   - Model name: {generator.model_name}")
        print(f"   - Expected dimension: {generator.embedding_dim}")
        logger.info("   - Model name: %s", generator.model_name)
        logger.info("   - Expected dimension: %d", generator.embedding_dim)
        
        # Force synchronous model loading
        print("   - Loading model weights...")
        logger.info("   - Loading model weights...")
        success = generator.load_model_now()
        model_time = time.time() - model_start

        if not success:
            # Embeddings were expected but model could not be loaded → abort.
            print(
                f"❌ Failed to load embedding model after {model_time:.2f}s – aborting startup"
            )
            logger.critical(
                "Embedding model missing or failed to load; exiting to prevent zero-vector indexing"
            )
            raise RuntimeError("Embedding model failed to load; startup aborted")

        print(f"✅ Embedding model loaded successfully in {model_time:.2f}s")
        print(f"   - Model: {generator.model_name}")
        print(f"   - Dimension: {generator.embedding_dim}")
        print("   - Status: Ready for semantic search")
        logger.info(
            "✅ Embedding model loaded successfully in %.2fs", model_time
        )
        logger.info("   - Model: %s", generator.model_name)
        logger.info("   - Dimension: %d", generator.embedding_dim)
        logger.info("   - Status: Ready for semantic search")
    except Exception as exc:
        model_time = time.time() - model_start
        print(f"❌ Failed to preload embedding model after {model_time:.2f}s: {exc}")
        print("   - Fallback: Text-based search will be used")
        logger.error("❌ Failed to preload embedding model after %.2fs: %s", model_time, exc)
        logger.error("   - Fallback: Text-based search will be used")

    # Start maintenance service
    maintenance_service = MaintenanceService()
    maintenance_service.start_background_service()
    app.state.maintenance_service = maintenance_service
    
    startup_time = time.time() - startup_start
    print(f"🎉 Serena server startup completed in {startup_time:.2f}s")
    logger.info("🎉 Serena server startup completed in %.2fs", startup_time)
    
    yield
    
    # Graceful shutdown with proper timeout handling
    import signal
    import asyncio
    
    shutdown_start = time.time()
    print("🛑 Serena server shutting down gracefully...")
    logger.info("🛑 Serena server shutting down gracefully...")
    
    shutdown_tasks = []
    
    # Shutdown maintenance service
    if hasattr(app.state, 'maintenance_service') and app.state.maintenance_service:
        print("   - Stopping maintenance service...")
        logger.info("   - Stopping maintenance service...")
        try:
            app.state.maintenance_service.stop()
            print("   ✅ Maintenance service stopped")
            logger.info("   ✅ Maintenance service stopped")
        except Exception as exc:
            print(f"   ⚠️ Maintenance service shutdown error: {exc}")
            logger.warning("   ⚠️ Maintenance service shutdown error: %s", exc)
    
    # Shutdown write queue gracefully with better error handling
    print("   - Shutting down write queue...")
    logger.info("   - Shutting down write queue...")
    try:
        from serena.infrastructure.write_queue import write_queue
        
        # Get current queue status before shutdown
        metrics = write_queue.get_metrics()
        pending_ops = metrics.current_queue_size
        
        if pending_ops > 0:
            print(f"   - Waiting for {pending_ops} pending operations...")
            logger.info(f"   - Waiting for {pending_ops} pending operations...")
        
        # Attempt graceful shutdown with timeout
        shutdown_timeout = min(30.0, max(10.0, pending_ops * 0.5))  # Dynamic timeout
        shutdown_success = write_queue.shutdown(timeout=shutdown_timeout)
        
        if shutdown_success:
            print("   ✅ Write queue shutdown completed")
            logger.info("   ✅ Write queue shutdown completed")
        else:
            print(f"   ⚠️ Write queue shutdown timeout after {shutdown_timeout}s")
            logger.warning(f"   ⚠️ Write queue shutdown timeout after {shutdown_timeout}s")
            
            # Get final metrics to see what was lost
            final_metrics = write_queue.get_metrics()
            if final_metrics.current_queue_size > 0:
                print(f"   ⚠️ {final_metrics.current_queue_size} operations may have been lost")
                logger.warning(f"   ⚠️ {final_metrics.current_queue_size} operations may have been lost")
                
    except Exception as exc:
        print(f"   ❌ Write queue shutdown error: {exc}")
        logger.error("   ❌ Write queue shutdown error: %s", exc)
    
    # Close database connections
    print("   - Closing database connections...")
    logger.info("   - Closing database connections...")
    try:
        from serena.database.session import get_db_manager
        db_manager = get_db_manager()
        db_manager.close()
        print("   ✅ Database connections closed")
        logger.info("   ✅ Database connections closed")
    except Exception as exc:
        print(f"   ⚠️ Database cleanup error: {exc}")
        logger.warning("   ⚠️ Database cleanup error: %s", exc)
    
    # Final cleanup
    shutdown_time = time.time() - shutdown_start
    print(f"✅ Serena server shutdown completed in {shutdown_time:.2f}s")
    logger.info(f"✅ Serena server shutdown completed in {shutdown_time:.2f}s")


async def _upsert_archive_direct(
    db: Session,
    task_id: str,
    markdown_text: str,
    filepath: Optional[str] = None,
    title: Optional[str] = None,
    kind: Optional['TaskKind'] = None,
    status: Optional['TaskStatus'] = None,
    completed_at: Optional[datetime] = None,
    async_write: bool = True
) -> bool:
    """Direct archive upsert without using Memory class."""
    
    def _upsert_internal():
        # Pre-process & chunk content for embeddings
        clean_content = preprocess_content(markdown_text)
        chunks = chunk_content(clean_content)
        
        # Extract title if not provided
        if not title:
            for line in markdown_text.splitlines():
                if line.startswith("#"):
                    title = line.lstrip("# ").strip()
                    break
        
        try:
            # Upsert main archive row with row-level locking
            archive = (
                db.query(Archive)
                .filter_by(task_id=task_id)
                .with_for_update()
                .first()
            )

            if archive:
                # Update existing archive
                archive.title = title or f"Archive {task_id}"
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
                    title=title or f"Archive {task_id}",
                    filepath=filepath or f"archive-{task_id}.md",
                    sha256=compute_content_hash(markdown_text),
                    kind=kind.value if kind else "archive",
                    status=status.value if status else None,
                    completed_at=completed_at,
                    summary=generate_summary(markdown_text),
                )
                db.add(archive)

            # Delete existing embeddings for this task
            db.query(Embedding).filter_by(task_id=task_id).delete()

            # Add new embeddings
            generator = get_default_generator()
            if chunks and generator.model is not None:
                embeddings = generator.generate_embeddings_batch(
                    [chunk for chunk, _ in chunks]
                )
                try:
                    for (chunk_text, chunk_pos), vector in zip(chunks, embeddings):
                        from serena.core.models import EmbeddingRecord

                        embedding_record = EmbeddingRecord.from_vector(
                            task_id=task_id,
                            vector=vector,
                            chunk_id=chunk_pos,
                            position=0,
                        )

                        embedding = Embedding(
                            task_id=embedding_record.task_id,
                            chunk_id=embedding_record.chunk_id,
                            position=embedding_record.position,
                            vector=embedding_record.vector,
                        )
                        db.add(embedding)
                finally:
                    # Ensure memory cleanup
                    del embeddings

            # Update FTS search index
            try:
                from sqlalchemy import text
                # Delete existing FTS entry
                db.execute(
                    text("DELETE FROM archives_fts WHERE task_id = :task_id"), 
                    {"task_id": task_id}
                )
                # Insert updated FTS entry
                db.execute(
                    text("INSERT INTO archives_fts (task_id, title, summary) VALUES (:task_id, :title, :summary)"),
                    {"task_id": archive.task_id, "title": archive.title, "summary": archive.summary or ""}
                )
            except Exception as fts_exc:
                # FTS index update is not critical
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to update FTS index for task {task_id}: {fts_exc}")

            # Commit the transaction
            db.commit()
            return True
            
        except Exception as exc:
            db.rollback()
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Database error during upsert for {task_id}: {exc}")
            return False
    
    if async_write:
        try:
            operation_id = write_queue.submit(
                _upsert_internal,
                priority=1,
                operation_type=WriteOperationType.UPSERT,
            )
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Queued async upsert for task {task_id} with operation ID {operation_id}")
            return True
        except Exception as exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to queue async upsert for task {task_id}: {exc}")
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
            allow_origins=settings.cors_origins_list if not settings.is_production else ["https://yourdomain.com"],
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
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
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
            logger.warning(
                "Serena exception in %s %s: %s",
                request.method,
                request.url.path,
                e.message
            )
            error_response = e.to_dict()
            return JSONResponse(
                status_code=500,
                content=error_response
            )
        except HTTPException as e:
            # Convert FastAPI HTTPExceptions to structured format
            if e.status_code >= 500:
                logger.error(
                    "HTTP exception in %s %s: %s",
                    request.method,
                    request.url.path,
                    e.detail
                )
            else:
                logger.warning(
                    "HTTP exception in %s %s: %s",
                    request.method,
                    request.url.path,
                    e.detail
                )
            
            error_response = create_error_response(
                code=ErrorCode.INTERNAL_ERROR,
                message=e.detail,
                operation=f"{request.method} {request.url.path}"
            )
            return JSONResponse(
                status_code=e.status_code,
                content=error_response
            )
        except Exception as e:
            # Handle unexpected exceptions with full logging
            error_id = str(uuid.uuid4())[:8]
            logger.error(
                "Unexpected error [%s] in %s %s: %s\n%s",
                error_id,
                request.method,
                request.url.path,
                str(e),
                traceback.format_exc() if settings.log_level.upper() == "DEBUG" else ""
            )
            
            error_response = create_error_response(
                code=ErrorCode.INTERNAL_ERROR,
                message="An unexpected error occurred" if settings.is_production else str(e),
                operation=f"{request.method} {request.url.path}",
                details={
                    "error_id": error_id,
                    "traceback": traceback.format_exc() if not settings.is_production else None
                }
            )
            return JSONResponse(
                status_code=500,
                content=error_response
            )
    
    # Add timing middleware
    @app.middleware("http")
    async def add_timing_header(request, call_next):
        import time
        import logging
        
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add execution time to response headers
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        # Log execution time for API endpoints (skip probe endpoints)
        if request.url.path not in ["/", "/health", "/ready", "/live"]:  # Skip root and health check
            # Build full URL with query parameters
            url_with_query = str(request.url.path)
            if request.url.query:
                url_with_query += "?" + request.url.query
            
            # Use print for immediate visibility
            print(f"{request.method} {url_with_query} - {process_time:.4f}s - {response.status_code}")
            
            # Also log via logger
            logger = logging.getLogger("serena.api")
            logger.info(
                "%s %s - %.4fs - %d",
                request.method,
                url_with_query,
                process_time,
                response.status_code
            )
        
        return response
    
    # Dependency for database session
    def get_db():
        with get_db_session() as session:
            yield session
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return create_success_response(
            data={"message": "Serena Memory Bridge API", "version": "0.1.0"}
        )
    
    @app.get("/health")
    async def health_check():
        """Enhanced health check endpoint with comprehensive system monitoring."""
        import psutil
        import os
        from pathlib import Path
        
        start_time = time.time()
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "0.1.0",
            "checks": {},
            "metrics": {},
            "warnings": []
        }
        
        # Database health check with detailed metrics
        try:
            from serena.database.session import get_db_session
            db_start = time.time()
            with get_db_session() as session:
                from sqlalchemy import text
                # Test basic connectivity
                session.execute(text("SELECT 1")).fetchone()
                
                # Get database size and stats
                db_path = Path(settings.memory_db)
                db_size_mb = db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0
                
                # Get table counts
                archive_count = session.execute(text("SELECT COUNT(*) FROM archives")).scalar()
                embedding_count = session.execute(text("SELECT COUNT(*) FROM embeddings")).scalar()
                
                db_response_time = (time.time() - db_start) * 1000
                
                health_data["checks"]["database"] = {
                    "status": "healthy",
                    "response_time_ms": round(db_response_time, 2),
                    "path": str(db_path),
                    "size_mb": round(db_size_mb, 2),
                    "archive_count": archive_count,
                    "embedding_count": embedding_count
                }
                
                # Warn if database is getting large
                if db_size_mb > 500:
                    health_data["warnings"].append(f"Database size is {db_size_mb:.1f}MB - consider maintenance")
                    
        except Exception as e:
            health_data["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "unhealthy"
        
        # Embedding model health check
        try:
            from serena.infrastructure.embeddings import get_default_generator
            embedding_start = time.time()
            generator = get_default_generator()
            
            if generator.model is not None:
                # Test embedding generation
                test_embedding = generator.generate_embeddings_batch(["health check test"])
                embedding_response_time = (time.time() - embedding_start) * 1000
                
                health_data["checks"]["embeddings"] = {
                    "status": "healthy",
                    "model": generator.model_name,
                    "dimension": generator.embedding_dim,
                    "response_time_ms": round(embedding_response_time, 2),
                    "test_vector_length": len(test_embedding[0]) if test_embedding else 0
                }
            else:
                health_data["checks"]["embeddings"] = {
                    "status": "degraded",
                    "message": "Model not loaded, using fallback search"
                }
                health_data["warnings"].append("Embedding model not available - only text search will work")
                
        except Exception as e:
            health_data["checks"]["embeddings"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["warnings"].append("Embedding service unavailable")
        
        # Write queue health check
        try:
            from serena.infrastructure.write_queue import write_queue
            queue_health = write_queue.health_check()
            health_data["checks"]["write_queue"] = queue_health
            
            if queue_health["status"] != "healthy":
                health_data["warnings"].extend(queue_health["issues"])
                
        except Exception as e:
            health_data["checks"]["write_queue"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # System metrics
        try:
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage(str(Path(settings.memory_db).parent))
            
            health_data["metrics"] = {
                "memory": {
                    "total_gb": round(memory_info.total / (1024**3), 2),
                    "available_gb": round(memory_info.available / (1024**3), 2),
                    "percent_used": memory_info.percent
                },
                "disk": {
                    "total_gb": round(disk_info.total / (1024**3), 2),
                    "free_gb": round(disk_info.free / (1024**3), 2),
                    "percent_used": round((disk_info.used / disk_info.total) * 100, 1)
                },
                "process": {
                    "pid": os.getpid(),
                    "cpu_percent": psutil.Process().cpu_percent(),
                    "memory_mb": round(psutil.Process().memory_info().rss / (1024**2), 2)
                }
            }
            
            # System warnings
            if memory_info.percent > 90:
                health_data["warnings"].append("System memory usage over 90%")
            if disk_info.free < 1024**3:  # Less than 1GB free
                health_data["warnings"].append("Less than 1GB disk space remaining")
                
        except Exception as e:
            health_data["warnings"].append(f"Could not collect system metrics: {e}")
        
        # Maintenance service health
        if hasattr(app.state, 'maintenance_service') and app.state.maintenance_service:
            maintenance_status = app.state.maintenance_service.get_status()
            health_data["checks"]["maintenance"] = maintenance_status
        else:
            health_data["checks"]["maintenance"] = {
                "status": "disabled",
                "message": "Maintenance service not running"
            }
        
        # Overall health determination
        total_response_time = (time.time() - start_time) * 1000
        health_data["response_time_ms"] = round(total_response_time, 2)
        
        # Determine overall status
        unhealthy_checks = [name for name, check in health_data["checks"].items() 
                           if check.get("status") == "unhealthy"]
        
        if unhealthy_checks:
            health_data["status"] = "unhealthy"
            return JSONResponse(
                status_code=503,
                content=create_error_response(
                    code=ErrorCode.SERVER_UNAVAILABLE,
                    message=f"Server is unhealthy: {', '.join(unhealthy_checks)}",
                    details=health_data
                )
            )
        elif health_data["warnings"]:
            health_data["status"] = "degraded"
        
        return create_success_response(data=health_data)
    
    @app.get("/ready")
    async def readiness_check():
        """Kubernetes-style readiness probe - is the service ready to serve traffic?"""
        try:
            from serena.database.session import get_db_session
            with get_db_session() as session:
                from sqlalchemy import text
                session.execute(text("SELECT 1")).fetchone()
            
            # Check if write queue is operational
            from serena.infrastructure.write_queue import write_queue
            queue_health = write_queue.health_check()
            
            if queue_health["status"] in ["healthy", "degraded"]:
                return create_success_response(data={"ready": True, "timestamp": datetime.now().isoformat()})
            else:
                return JSONResponse(
                    status_code=503,
                    content=create_error_response(
                        code=ErrorCode.SERVER_UNAVAILABLE,
                        message="Service not ready - write queue unhealthy"
                    )
                )
                
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content=create_error_response(
                    code=ErrorCode.SERVER_UNAVAILABLE,
                    message="Service not ready - database unavailable",
                    details={"error": str(e)}
                )
            )
    
    @app.get("/live")
    async def liveness_check():
        """Kubernetes-style liveness probe - is the service alive?"""
        # Simple check that the service is responding
        return create_success_response(data={
            "alive": True, 
            "timestamp": datetime.now().isoformat(),
            "pid": os.getpid()
        })
    
    @app.get("/maintenance/status")
    async def get_maintenance_status(request: "Request"):
        """Get the status of the maintenance service."""
        service = request.app.state.maintenance_service
        if not service:
            return create_error_response(
                code=ErrorCode.SERVER_UNAVAILABLE,
                message="Maintenance service not running",
                operation="maintenance_status"
            )
        return create_success_response(data=service.get_status())

    @app.post("/maintenance/run/{operation}")
    async def run_maintenance_operation(operation: str, request: "Request"):
        """Trigger a specific maintenance operation."""
        service = request.app.state.maintenance_service
        if not service:
            return create_error_response(
                code=ErrorCode.SERVER_UNAVAILABLE,
                message="Maintenance service not running",
                operation="maintenance_run"
            )
        try:
            service.run_operation(operation)
            return create_success_response(
                data={"message": f"Operation '{operation}' triggered successfully"}
            )
        except ValueError:
            return create_error_response(
                code=ErrorCode.INVALID_INPUT,
                message=f"Invalid operation: {operation}",
                operation="maintenance_run",
                details={"operation": operation}
            )
        except Exception as e:
            return create_error_response(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Operation failed: {str(e)}",
                operation="maintenance_run",
                details={"operation": operation, "error": str(e)}
            )

    @app.get("/archives")
    async def list_archives(
        limit: int = 20,
        offset: int = 0,
        db: Session = Depends(get_db)
    ):
        """List archived tasks."""
        try:
            # Validate parameters
            if limit < 1 or limit > 100:
                return create_error_response(
                    code=ErrorCode.INVALID_INPUT,
                    message="Limit must be between 1 and 100",
                    operation="list_archives",
                    details={"limit": limit}
                )
            
            if offset < 0:
                return create_error_response(
                    code=ErrorCode.INVALID_INPUT,
                    message="Offset must be non-negative",
                    operation="list_archives",
                    details={"offset": offset}
                )
            
            # Sort by latest completion date, with fallback to updated_at for NULL completed_at
            archives = db.query(Archive).order_by(
                Archive.completed_at.desc().nulls_last(),
                Archive.updated_at.desc()
            ).offset(offset).limit(limit).all()
            
            total_count = db.query(Archive).count()
            
            data = {
                "archives": [
                    {
                        "task_id": archive.task_id,
                        "title": archive.title,
                        "kind": archive.kind,
                        "status": archive.status,
                        "completed_at": archive.completed_at.isoformat() if archive.completed_at else None,
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
            
            return create_success_response(data=data)
        except Exception as e:
            return create_error_response(
                code=ErrorCode.DATABASE_QUERY_FAILED,
                message="Failed to retrieve archives",
                operation="list_archives",
                details={"error": str(e)}
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
                    operation="get_archive",
                    details={"task_id": task_id}
                )
            
            archive = db.query(Archive).filter(Archive.task_id == task_id).first()
            
            if not archive:
                return create_error_response(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message=f"Archive not found: {task_id}",
                    operation="get_archive",
                    details={"task_id": task_id}
                )
            
            data = {
                "task_id": archive.task_id,
                "title": archive.title,
                "filepath": archive.filepath,
                "sha256": archive.sha256,
                "kind": archive.kind,
                "status": archive.status,
                "completed_at": archive.completed_at.isoformat() if archive.completed_at else None,
                "summary": archive.summary,
                "created_at": archive.created_at.isoformat(),
                "updated_at": archive.updated_at.isoformat(),
                "embedding_version": archive.embedding_version,
                "last_embedded_at": archive.last_embedded_at.isoformat() if archive.last_embedded_at else None,
            }
            
            return create_success_response(data=data)
        except Exception as e:
            return create_error_response(
                code=ErrorCode.DATABASE_QUERY_FAILED,
                message="Failed to retrieve archive",
                operation="get_archive",
                details={"task_id": task_id, "error": str(e)}
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
                    operation="delete_archive",
                    details={"task_id": task_id}
                )
            
            archive = db.query(Archive).filter(Archive.task_id == task_id).first()
            
            if not archive:
                return create_error_response(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message=f"Archive not found: {task_id}",
                    operation="delete_archive",
                    details={"task_id": task_id}
                )
            
            # Store title before deletion
            title = archive.title
            
            # Delete the archive (embeddings will be cascade deleted)
            db.delete(archive)
            db.commit()
            
            return create_success_response(
                data={
                    "message": f"Archive {task_id} deleted successfully",
                    "task_id": task_id,
                    "title": title
                }
            )
        except Exception as e:
            db.rollback()
            return create_error_response(
                code=ErrorCode.DATABASE_TRANSACTION_FAILED,
                message="Failed to delete archive",
                operation="delete_archive",
                details={"task_id": task_id, "error": str(e)}
            )
    
    @app.get("/search")
    async def search_archives(
        q: str,
        limit: int = 10,
        threshold: float = 0.1,
        db: Session = Depends(get_db)
    ):
        """Search archives using semantic similarity."""
        try:
            # Validate parameters
            if not q or len(q.strip()) == 0:
                return create_error_response(
                    code=ErrorCode.INVALID_INPUT,
                    message="Search query cannot be empty",
                    operation="search_archives",
                    details={"query": q}
                )
            
            if limit < 1 or limit > 100:
                return create_error_response(
                    code=ErrorCode.INVALID_INPUT,
                    message="Limit must be between 1 and 100",
                    operation="search_archives",
                    details={"limit": limit}
                )
            
            if threshold < 0 or threshold > 1:
                return create_error_response(
                    code=ErrorCode.INVALID_INPUT,
                    message="Threshold must be between 0 and 1",
                    operation="search_archives",
                    details={"threshold": threshold}
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
                    "completed_at": result.completed_at.isoformat() if result.completed_at else None,
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
            
            return create_success_response(data=data)
            
        except Exception as exc:
            return create_error_response(
                code=ErrorCode.SEARCH_QUERY_FAILED,
                message="Search operation failed",
                operation="search_archives",
                details={"query": q, "error": str(exc)}
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
            
            return create_success_response(data=data)
        except Exception as e:
            return create_error_response(
                code=ErrorCode.DATABASE_QUERY_FAILED,
                message="Failed to retrieve statistics",
                operation="get_statistics",
                details={"error": str(e)}
            )
    
    @app.get("/queue/status")
    async def get_queue_status():
        """Get write queue status and metrics."""
        try:
            from serena.infrastructure.write_queue import write_queue
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
                "issues": health["issues"]
            }
            
            return create_success_response(data=data)
        except Exception as e:
            return create_error_response(
                code=ErrorCode.DEPENDENCY_ERROR,
                message="Failed to retrieve queue status",
                operation="get_queue_status",
                details={"error": str(e)}
            )
    
    @app.post("/archives")
    async def upsert_archive(
        request: dict,
        async_write: bool = None,  # Optional query parameter
        db: Session = Depends(get_db)
    ):
        """Upsert (insert or update) an archive using the server's embedding model."""
        try:
            from serena.cli.common import RemoteMemory
            from datetime import datetime
            from serena.core.models import TaskKind, TaskStatus
            
            # Extract data from request
            task_id = request.get('task_id')
            markdown_text = request.get('markdown_text')
            filepath = request.get('filepath')
            title = request.get('title')
            kind = request.get('kind', 'archive')
            status = request.get('status')
            completed_at = request.get('completed_at')
            
            # Handle async_write configuration - priority order:
            # 1. Request body parameter (for explicit control)
            # 2. Query parameter (for URL-based control)  
            # 3. Server configuration default
            request_async_write = request.get('async_write')
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
                    operation="upsert_archive",
                    details={"missing_field": "task_id"}
                )
            
            if not markdown_text:
                return create_error_response(
                    code=ErrorCode.MISSING_REQUIRED_FIELD,
                    message="markdown_text is required",
                    operation="upsert_archive",
                    details={"missing_field": "markdown_text"}
                )
            
            # Validate task_id format
            if len(task_id) > 255:
                return create_error_response(
                    code=ErrorCode.INVALID_TASK_ID,
                    message="Task ID must be 255 characters or less",
                    operation="upsert_archive",
                    details={"task_id": task_id, "length": len(task_id)}
                )
            
            # Validate content size
            if len(markdown_text) > 10 * 1024 * 1024:  # 10MB limit
                return create_error_response(
                    code=ErrorCode.CONTENT_TOO_LARGE,
                    message="Content exceeds maximum size limit (10MB)",
                    operation="upsert_archive",
                    details={"content_size": len(markdown_text)}
                )
            
            # Parse completed_at if provided
            parsed_completed_at = None
            if completed_at:
                try:
                    parsed_completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                except Exception:
                    return create_error_response(
                        code=ErrorCode.INVALID_INPUT,
                        message="Invalid completed_at format. Use ISO format.",
                        operation="upsert_archive",
                        details={"completed_at": completed_at}
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
                        operation="upsert_archive",
                        details={"kind": kind, "valid_values": [k.value for k in TaskKind]}
                    )
            
            task_status = None
            if status:
                try:
                    task_status = TaskStatus(status)
                except ValueError:
                    return create_error_response(
                        code=ErrorCode.INVALID_INPUT,
                        message=f"Invalid status value: {status}",
                        operation="upsert_archive",
                        details={"status": status, "valid_values": [s.value for s in TaskStatus]}
                    )
            
            # Log async write mode for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Upserting {task_id} with async_write={use_async_write}")
            
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
                async_write=use_async_write
            )
            
            if success:
                return create_success_response(
                    data={
                        "task_id": task_id,
                        "message": "Archive upserted successfully",
                        "async_write": use_async_write,
                        "processing": "queued" if use_async_write else "completed"
                    }
                )
            else:
                return create_error_response(
                    code=ErrorCode.INDEXING_FAILED,
                    message="Failed to upsert archive",
                    operation="upsert_archive",
                    details={"task_id": task_id}
                )
                
        except Exception as exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error upserting archive {task_id}: {exc}")
            return create_error_response(
                code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error during archive upsert",
                operation="upsert_archive",
                details={"task_id": task_id, "error": str(exc)}
            )
    
    @app.post("/generate-embeddings")
    async def generate_embeddings(
        texts: list[str],
        db: Session = Depends(get_db)
    ):
        """Generate embeddings using the server's pre-loaded model."""
        try:
            from serena.infrastructure.embeddings import get_default_generator
            
            # Validate input
            if not texts:
                return create_error_response(
                    code=ErrorCode.MISSING_REQUIRED_FIELD,
                    message="texts list is required",
                    operation="generate_embeddings",
                    details={"missing_field": "texts"}
                )
            
            if len(texts) > 100:
                return create_error_response(
                    code=ErrorCode.INVALID_INPUT,
                    message="Cannot process more than 100 texts at once",
                    operation="generate_embeddings",
                    details={"count": len(texts), "max_allowed": 100}
                )
            
            # Validate each text
            for i, text in enumerate(texts):
                if not isinstance(text, str):
                    return create_error_response(
                        code=ErrorCode.INVALID_INPUT,
                        message=f"Text at index {i} must be a string",
                        operation="generate_embeddings",
                        details={"index": i, "type": type(text).__name__}
                    )
                
                if len(text) > 8192:  # Model context limit
                    return create_error_response(
                        code=ErrorCode.CONTENT_TOO_LARGE,
                        message=f"Text at index {i} exceeds maximum length (8192 characters)",
                        operation="generate_embeddings",
                        details={"index": i, "length": len(text)}
                    )
            
            generator = get_default_generator()
            if generator.model is None:
                return create_error_response(
                    code=ErrorCode.EMBEDDING_SERVICE_UNAVAILABLE,
                    message="Embedding model not available",
                    operation="generate_embeddings"
                )
            
            embeddings = generator.generate_embeddings_batch(texts)
            
            return create_success_response(
                data={
                    "embeddings": embeddings,
                    "model": generator.model_name,
                    "count": len(embeddings)
                }
            )
        except Exception as exc:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating embeddings: {exc}")
            return create_error_response(
                code=ErrorCode.EMBEDDING_GENERATION_FAILED,
                message="Failed to generate embeddings",
                operation="generate_embeddings",
                details={"error": str(exc)}
            )
    
    @app.get("/metrics")
    async def get_metrics():
        """Get comprehensive system metrics for monitoring."""
        try:
            import psutil
            from pathlib import Path
            
            # Collect system metrics
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage(str(Path(settings.memory_db).parent))
            process = psutil.Process()
            
            # Database metrics
            from serena.database.session import get_db_manager
            db_manager = get_db_manager()
            db_health = db_manager.health_check()
            
            # Write queue metrics
            from serena.infrastructure.write_queue import write_queue
            queue_metrics = write_queue.get_metrics()
            queue_health = write_queue.health_check()
            
            # Maintenance service metrics
            maintenance_metrics = {}
            if hasattr(app.state, 'maintenance_service') and app.state.maintenance_service:
                maintenance_metrics = app.state.maintenance_service.get_status()
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "memory": {
                        "total_gb": round(memory_info.total / (1024**3), 2),
                        "available_gb": round(memory_info.available / (1024**3), 2),
                        "percent_used": memory_info.percent
                    },
                    "disk": {
                        "total_gb": round(disk_info.total / (1024**3), 2),
                        "free_gb": round(disk_info.free / (1024**3), 2),
                        "percent_used": round((disk_info.used / disk_info.total) * 100, 1)
                    },
                    "process": {
                        "pid": process.pid,
                        "cpu_percent": process.cpu_percent(),
                        "memory_mb": round(process.memory_info().rss / (1024**2), 2),
                        "threads": process.num_threads(),
                        "open_files": len(process.open_files()),
                        "create_time": process.create_time()
                    }
                },
                "database": db_health.get("metrics", {}),
                "write_queue": {
                    "metrics": {
                        "total_operations": queue_metrics.total_operations,
                        "successful_operations": queue_metrics.successful_operations,
                        "failed_operations": queue_metrics.failed_operations,
                        "current_queue_size": queue_metrics.current_queue_size,
                        "avg_processing_time_ms": queue_metrics.avg_processing_time_ms
                    },
                    "health": queue_health
                },
                "maintenance": maintenance_metrics,
                "deployment": settings.get_deployment_info()
            }
            
            return create_success_response(data=metrics)
            
        except Exception as e:
            return create_error_response(
                code=ErrorCode.INTERNAL_ERROR,
                message="Failed to collect metrics",
                operation="get_metrics",
                details={"error": str(e)}
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
            
            return create_success_response(data=settings_dict)
        except Exception as e:
            return create_error_response(
                code=ErrorCode.CONFIGURATION_ERROR,
                message="Failed to retrieve settings",
                operation="get_settings",
                details={"error": str(e)}
            )
    
    @app.get("/deployment/info")
    async def get_deployment_info():
        """Get deployment and environment information."""
        try:
            return create_success_response(data=settings.get_deployment_info())
        except Exception as e:
            return create_error_response(
                code=ErrorCode.CONFIGURATION_ERROR,
                message="Failed to retrieve deployment info",
                operation="get_deployment_info",
                details={"error": str(e)}
            )
    
    return app