"""FastAPI server for Serena memory bridge API."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from serena.infrastructure.session import get_db_session
from serena.core.models import Archive, Embedding, SearchResult
from sqlalchemy.orm import Session


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Serena Memory Bridge API",
        description="API for accessing and managing task memory archives with semantic search",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Dependency for database session
    def get_db() -> Session:
        with get_db_session() as session:
            yield session
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "Serena Memory Bridge API", "version": "0.1.0"}
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        from serena.infrastructure.session import get_db_manager
        
        db_manager = get_db_manager()
        is_healthy = db_manager.health_check()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "database": "connected" if is_healthy else "disconnected"
        }
    
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
        threshold: float = 0.7,
        db: Session = Depends(get_db)
    ):
        """Search archives using semantic similarity."""
        # For now, implement simple text search
        # TODO: Implement proper semantic search with embeddings
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