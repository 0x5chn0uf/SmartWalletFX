"""FastAPI server for Serena memory bridge API."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from serena.database.session import get_db_session
from serena.core.models import Archive, Embedding, SearchResult
from sqlalchemy.orm import Session


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    import logging
    import time
    from serena.infrastructure.embeddings import get_default_generator
    from serena import config
    
    # Use both print and logging to ensure visibility
    print("🚀 Serena server startup beginning...")
    
    logger = logging.getLogger("serena.server")
    logger.setLevel(logging.INFO)
    startup_start = time.time()
    
    print("📋 Configuration check:")
    print(f"   - Embeddings enabled: {config.embeddings_enabled()}")
    print(f"   - Database path: {config.memory_db_path()}")
    
    logger.info("🚀 Serena server startup beginning...")
    logger.info("📋 Configuration check:")
    logger.info("   - Embeddings enabled: %s", config.embeddings_enabled())
    logger.info("   - Database path: %s", config.memory_db_path())
    
    if config.embeddings_enabled():
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
            
            if success:
                print(f"✅ Embedding model loaded successfully in {model_time:.2f}s")
                print(f"   - Model: {generator.model_name}")
                print(f"   - Dimension: {generator.embedding_dim}")
                print("   - Status: Ready for semantic search")
                logger.info("✅ Embedding model loaded successfully in %.2fs", model_time)
                logger.info("   - Model: %s", generator.model_name)
                logger.info("   - Dimension: %d", generator.embedding_dim)
                logger.info("   - Status: Ready for semantic search")
            else:
                print(f"⚠️ Embedding model failed to load after {model_time:.2f}s")
                print("   - Fallback: Text-based search will be used")
                logger.warning("⚠️ Embedding model failed to load after %.2fs", model_time)
                logger.warning("   - Fallback: Text-based search will be used")
        except Exception as exc:
            model_time = time.time() - model_start
            print(f"❌ Failed to preload embedding model after {model_time:.2f}s: {exc}")
            print("   - Fallback: Text-based search will be used")
            logger.error("❌ Failed to preload embedding model after %.2fs: %s", model_time, exc)
            logger.error("   - Fallback: Text-based search will be used")
    else:
        print("ℹ️ Embeddings disabled via configuration")
        print("   - Search mode: Text-based only")
        logger.info("ℹ️ Embeddings disabled via configuration")
        logger.info("   - Search mode: Text-based only")
    
    startup_time = time.time() - startup_start
    print(f"🎉 Serena server startup completed in {startup_time:.2f}s")
    logger.info("🎉 Serena server startup completed in %.2fs", startup_time)
    
    yield
    
    # Shutdown
    print("🛑 Serena server shutting down...")
    logger.info("🛑 Serena server shutting down...")    # Shutdown


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Serena Memory Bridge API",
        description="API for accessing and managing task memory archives with semantic search",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # Configure CORS
    from serena.config import cors_origins, cors_allow_credentials, cors_allow_methods, cors_allow_headers
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins(),
        allow_credentials=cors_allow_credentials(),
        allow_methods=cors_allow_methods(),
        allow_headers=[cors_allow_headers()],
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
        
        # Log execution time for API endpoints
        logger = logging.getLogger("serena.api")
        if request.url.path not in ["/", "/health"]:  # Skip root and health check
            # Build full URL with query parameters
            url_with_query = str(request.url.path)
            if request.url.query:
                url_with_query += "?" + request.url.query
            
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
        return {"message": "Serena Memory Bridge API", "version": "0.1.0"}
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        from serena.infrastructure.embeddings import get_default_generator
        from serena import config
        from pathlib import Path
        
        # Simple database health check
        try:
            from serena.database.session import get_db_session
            with get_db_session() as session:
                from sqlalchemy import text
                session.execute(text("SELECT 1")).fetchone()
                is_db_healthy = True
        except Exception:
            is_db_healthy = False
        
        # Check embedding model status
        embedding_status = "disabled"
        model_name = None
        if config.embeddings_enabled():
            try:
                generator = get_default_generator()
                if generator.model is not None:
                    embedding_status = "loaded"
                    model_name = generator.model_name
                else:
                    embedding_status = "failed"
            except Exception:
                embedding_status = "error"
        
        overall_healthy = is_db_healthy and (embedding_status in ["loaded", "disabled"])
        
        response = {
            "status": "healthy" if overall_healthy else "unhealthy",
            "database": "connected" if is_db_healthy else "disconnected",
            "embeddings": {
                "status": embedding_status,
                "model": model_name,
                "enabled": config.embeddings_enabled()
            },
            "version": "0.1.0"
        }
        
        return response
    
    @app.get("/archives")
    async def list_archives(
        limit: int = 20,
        offset: int = 0,
        db: Session = Depends(get_db)
    ):
        """List archived tasks."""
        archives = db.query(Archive).offset(offset).limit(limit).all()
        
        return {
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
                }
                for archive in archives
            ],
            "total": db.query(Archive).count(),
            "limit": limit,
            "offset": offset,
        }
    
    @app.get("/archives/{task_id}")
    async def get_archive(task_id: str, db: Session = Depends(get_db)):
        """Get specific archive by task ID."""
        archive = db.query(Archive).filter(Archive.task_id == task_id).first()
        
        if not archive:
            raise HTTPException(status_code=404, detail="Archive not found")
        
        return {
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
    
    @app.get("/search")
    async def search_archives(
        q: str,
        limit: int = 10,
        threshold: float = 0.1,
        db: Session = Depends(get_db)
    ):
        """Search archives using semantic similarity."""
        from serena.services.memory_impl import Memory
        
        try:
            memory = Memory()
            search_results = memory.search(query=q, k=limit)
            
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
            
            return {
                "query": q,
                "results": results,
                "total": len(results),
                "threshold": threshold,
            }
        except Exception as exc:
            # Fallback to simple text search if semantic search fails
            archives = (
                db.query(Archive)
                .filter(
                    Archive.title.contains(q) | 
                    Archive.summary.contains(q)
                )
                .limit(limit)
                .all()
            )
            
            results = [
                {
                    "task_id": archive.task_id,
                    "title": archive.title,
                    "score": 1.0,  # Placeholder score
                    "excerpt": archive.summary or archive.title,
                    "kind": archive.kind,
                    "status": archive.status,
                    "completed_at": archive.completed_at.isoformat() if archive.completed_at else None,
                    "filepath": archive.filepath,
                }
                for archive in archives
            ]
            
            return {
                "query": q,
                "results": results,
                "total": len(results),
                "threshold": threshold,
                "fallback": True,
                "error": str(exc),
            }
    
    @app.get("/stats")
    async def get_statistics(db: Session = Depends(get_db)):
        """Get database statistics."""
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
        
        return {
            "total_archives": archive_count,
            "total_embeddings": embedding_count,
            "by_kind": kind_counts,
            "by_status": status_counts,
        }
    
    return app