"""Embedding generation and utilities.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from functools import lru_cache
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Handles embedding generation using sentence-transformers."""

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        self.model_name = model_name or os.getenv(
            "SERENA_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self._model: "Optional[sentence_transformers.SentenceTransformer]" = None
        self._loading_thread: Optional[threading.Thread] = None
        self.embedding_dim = 384  # Default for MiniLM
        self._device = device or self._detect_optimal_device()
        self._lock = threading.Lock()  # Thread safety for model loading
        
        # Model lifecycle management
        self._last_used = time.time()
        self._cleanup_timer: Optional[threading.Timer] = None
        self._idle_timeout = 900  # 15 minutes idle timeout
        self._cleanup_enabled = True
        
        # Performance monitoring
        self._usage_stats = {
            "total_requests": 0,
            "batch_requests": 0,
            "total_processing_time": 0.0,
            "last_cleanup": None,
            "memory_peak_mb": 0.0
        }
        
        logger.info("EmbeddingGenerator initialized with device: %s, idle_timeout: %ds", 
                   self._device, self._idle_timeout)

    # ------------------------------------------------------------------
    # Device detection
    # ------------------------------------------------------------------
    def _detect_optimal_device(self) -> str:
        """Detect the optimal device for embedding generation."""
        # Check environment variable override
        env_device = os.getenv("SERENA_DEVICE")
        if env_device:
            logger.info("Using device from environment: %s", env_device)
            return env_device
        
        # Check for CUDA availability
        try:
            import torch
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
                logger.info("GPU detected: %s (count: %d)", gpu_name, gpu_count)
                return "cuda"
        except ImportError:
            logger.debug("PyTorch not available, checking for MPS...")
        except Exception as exc:
            logger.warning("CUDA check failed: %s", exc)
        
        # Check for MPS (Apple Silicon) availability
        try:
            import torch
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                logger.info("MPS (Apple Silicon) detected")
                return "mps"
        except (ImportError, AttributeError):
            logger.debug("MPS not available")
        except Exception as exc:
            logger.warning("MPS check failed: %s", exc)
        
        logger.info("Using CPU fallback")
        return "cpu"
    
    # ------------------------------------------------------------------
    # Lazy load
    # ------------------------------------------------------------------
    @property
    def model(self):  # noqa: D401
        if self._model is None:
            with self._lock:  # Thread-safe model loading
                if self._model is None:  # Double-check after acquiring lock
                    # Avoid blocking event loop
                    in_loop = False
                    try:
                        asyncio.get_running_loop()
                        in_loop = True
                    except RuntimeError:
                        pass

                    if in_loop:
                        if not self._loading_thread or not self._loading_thread.is_alive():
                            self._loading_thread = threading.Thread(
                                target=self._load_model_sync,
                                daemon=True,
                                name="embedding-model-loader",
                            )
                            self._loading_thread.start()
                        return None
                    self._load_model_sync()
        return self._model

    def load_model_now(self) -> bool:
        """Force synchronous model loading, waiting for completion if needed."""
        if self._model is not None:
            return True  # Already loaded

        # If we're in an async context and threading is being used
        if self._loading_thread and self._loading_thread.is_alive():
            logger.info("Waiting for background model loading to complete...")
            self._loading_thread.join(timeout=30)  # Wait up to 30 seconds

        # If still not loaded, force synchronous loading
        if self._model is None:
            self._load_model_sync()

        return self._model is not None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_model_sync(self) -> None:  # noqa: WPS213
        try:
            import numpy as _np

            if int(_np.__version__.split(".")[0]) >= 2:
                logger.warning(
                    "NumPy %s incompatible with sentence-transformers", _np.__version__
                )
                return
        except Exception:
            pass

        try:
            from sentence_transformers import SentenceTransformer  # noqa: WPS433
            from pathlib import Path

            # Use local cache directory for faster loading
            cache_dir = Path.home() / ".cache" / "serena" / "models"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info("Loading embedding model: %s", self.model_name)
            logger.debug("Using cache directory: %s", cache_dir)
            
            # Load with local cache and device optimization
            logger.info("Loading model on device: %s", self._device)
            self._model = SentenceTransformer(
                self.model_name,
                cache_folder=str(cache_dir),
                device=self._device,
            )
            
            # Verify device assignment
            actual_device = getattr(self._model.device, 'type', str(self._model.device))
            if actual_device != self._device and self._device != "cpu":
                logger.warning(
                    "Model loaded on %s instead of requested %s, falling back to CPU",
                    actual_device, self._device
                )
                # Reload on CPU if GPU failed
                self._model = SentenceTransformer(
                    self.model_name,
                    cache_folder=str(cache_dir),
                    device="cpu",
                )
                self._device = "cpu"
            
            logger.info("Model successfully loaded on device: %s", self._device)
        except ImportError:
            logger.warning("sentence-transformers not installed – embeddings disabled")
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to load embedding model: %s", exc)

    
    # ------------------------------------------------------------------
    # Model lifecycle management
    # ------------------------------------------------------------------
    def _update_usage_stats(self, processing_time: float, is_batch: bool = False) -> None:
        """Update usage statistics and trigger cleanup timer reset."""
        self._last_used = time.time()
        self._usage_stats["total_requests"] += 1
        self._usage_stats["total_processing_time"] += processing_time
        
        if is_batch:
            self._usage_stats["batch_requests"] += 1
        
        # Reset cleanup timer
        self._reset_cleanup_timer()
        
        # Monitor memory usage (optional, lightweight check)
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            if memory_mb > self._usage_stats["memory_peak_mb"]:
                self._usage_stats["memory_peak_mb"] = memory_mb
        except ImportError:
            pass  # psutil not available, skip memory monitoring
        except Exception:
            pass  # Ignore memory monitoring errors
    
    def _reset_cleanup_timer(self) -> None:
        """Reset the model cleanup timer."""
        if not self._cleanup_enabled:
            return
            
        # Cancel existing timer
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
            
        # Start new timer
        self._cleanup_timer = threading.Timer(
            self._idle_timeout, 
            self._cleanup_model_if_idle
        )
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()
    
    def _cleanup_model_if_idle(self) -> None:
        """Clean up model if it has been idle for too long."""
        if not self._cleanup_enabled:
            return
            
        current_time = time.time()
        idle_time = current_time - self._last_used
        
        # Only cleanup if truly idle and cleanup is still enabled
        if idle_time >= self._idle_timeout and self._model is not None:
            logger.info(
                "Cleaning up embedding model after %.1f minutes of inactivity",
                idle_time / 60
            )
            
            with self._lock:
                # Double-check in case model was used between timer fire and lock acquisition
                if current_time - self._last_used >= self._idle_timeout:
                    try:
                        # Free model memory
                        if self._model is not None:
                            # Try to free GPU memory if applicable
                            try:
                                if hasattr(self._model, 'device') and 'cuda' in str(self._model.device):
                                    import torch
                                    torch.cuda.empty_cache()
                            except Exception:
                                pass  # Ignore GPU cleanup errors
                            
                            # Clear model reference
                            self._model = None
                            
                        # Record cleanup time
                        self._usage_stats["last_cleanup"] = current_time
                        
                        logger.debug("Embedding model cleanup completed")
                        
                    except Exception as exc:
                        logger.warning("Model cleanup failed: %s", exc)
    
    def get_usage_stats(self) -> dict:
        """Get current usage statistics."""
        current_time = time.time()
        return {
            **self._usage_stats,
            "model_loaded": self._model is not None,
            "idle_time_seconds": current_time - self._last_used,
            "device": self._device,
            "cleanup_enabled": self._cleanup_enabled,
        }
    
    def disable_cleanup(self) -> None:
        """Disable automatic model cleanup (useful for high-frequency usage)."""
        self._cleanup_enabled = False
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
            self._cleanup_timer = None
        logger.info("Model cleanup disabled")
    
    def enable_cleanup(self, idle_timeout: Optional[int] = None) -> None:
        """Enable automatic model cleanup with optional timeout override."""
        self._cleanup_enabled = True
        if idle_timeout is not None:
            self._idle_timeout = idle_timeout
        self._reset_cleanup_timer()
        logger.info("Model cleanup enabled with %d second timeout", self._idle_timeout)
    
    def force_cleanup(self) -> bool:
        """Force immediate model cleanup, returns True if model was cleaned up."""
        if self._model is None:
            return False
            
        with self._lock:
            if self._model is not None:
                try:
                    # Cancel any pending cleanup timer
                    if self._cleanup_timer:
                        self._cleanup_timer.cancel()
                        self._cleanup_timer = None
                    
                    # Free GPU memory if applicable
                    try:
                        if hasattr(self._model, 'device') and 'cuda' in str(self._model.device):
                            import torch
                            torch.cuda.empty_cache()
                    except Exception:
                        pass
                    
                    self._model = None
                    self._usage_stats["last_cleanup"] = time.time()
                    
                    logger.info("Forced embedding model cleanup completed")
                    return True
                    
                except Exception as exc:
                    logger.error("Forced cleanup failed: %s", exc)
                    
        return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_embedding(self, text: str) -> List[float]:
        if not text.strip():
            return [0.0] * self.embedding_dim

        if self.model is None:
            # Embedding model was expected but failed to load – abort early.
            raise RuntimeError("Embedding model not loaded; aborting pipeline")

        # Happy-path: model present
        vec = self.model.encode(text, convert_to_numpy=True)  # type: ignore[attr-defined]
        result = vec.tolist()
        del vec  # Explicit cleanup of numpy array
        return result

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self.model is None:
            raise RuntimeError("Embedding model not loaded; aborting pipeline")

        # Happy-path batch encode – any exception bubbles up to caller
        logger.debug("Starting batch encoding for %d texts", len(texts))
        vecs = self.model.encode(texts, convert_to_numpy=True, batch_size=32)  # type: ignore[attr-defined]
        logger.debug("Batch encode successful (shape=%s)", getattr(vecs, 'shape', 'unknown'))
        
        # Convert to list and explicitly delete numpy array to free memory
        result = vecs.tolist()
        del vecs  # Explicit cleanup of large numpy array
        
        return result


# ------------------------------------------------------------------
# Helper functions (unchanged)
# ------------------------------------------------------------------


def chunk_content(content: str, max_chunk_size: int = 4096) -> List[tuple]:
    if len(content) <= max_chunk_size:
        return [(content, 0)]

    paragraphs = content.split("\n\n")
    chunks: list[tuple[str, int]] = []
    current = ""
    pos = 0
    for para in paragraphs:
        if len(para) > max_chunk_size:
            for sentence in para.split(". "):
                if len(current) + len(sentence) > max_chunk_size and current:
                    chunks.append((current.strip(), pos))
                    pos += len(current)
                    current = sentence + ". "
                else:
                    current += sentence + ". "
        else:
            if len(current) + len(para) > max_chunk_size and current:
                chunks.append((current.strip(), pos))
                pos += len(current)
                current = para + "\n\n"
            else:
                current += para + "\n\n"
    if current.strip():
        chunks.append((current.strip(), pos))
    return chunks


def preprocess_content(content: str) -> str:
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]
    content = (
        content.replace("```", "").replace("**", "").replace("*", "").replace("#", "")
    )
    return " ".join(line.strip() for line in content.split("\n") if line.strip())


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    try:
        a = np.array(v1, dtype=np.float32)
        b = np.array(v2, dtype=np.float32)
        n1 = np.linalg.norm(a)
        n2 = np.linalg.norm(b)
        if n1 == 0 or n2 == 0:
            # Cleanup arrays before returning
            del a, b
            return 0.0
        result = float(np.dot(a, b) / (n1 * n2))
        # Explicit cleanup of numpy arrays
        del a, b
        return result
    except Exception as exc:
        logger.error("Cosine similarity error: %s", exc)
        return 0.0


def batch_cosine_similarity(
    query_vec: List[float], vectors: List[List[float]]
) -> List[float]:
    try:
        q = np.array(query_vec, dtype=np.float32)
        mat = np.array(vectors, dtype=np.float32)
        qn = np.linalg.norm(q)
        if qn == 0:
            # Cleanup arrays before returning
            del q, mat
            return [0.0] * len(vectors)
        q /= qn
        norms = np.linalg.norm(mat, axis=1)
        norms[norms == 0] = 1
        mat = mat / norms[:, np.newaxis]
        result = np.dot(mat, q).tolist()
        # Explicit cleanup of numpy arrays
        del q, mat, norms
        return result
    except Exception as exc:
        logger.error("Batch cosine similarity error: %s", exc)
        return [0.0] * len(vectors)


@lru_cache(maxsize=1)
def get_default_generator() -> EmbeddingGenerator:
    return EmbeddingGenerator()


@lru_cache(maxsize=1024)
def generate_embedding(text: str) -> List[float]:
    return get_default_generator().generate_embedding(text)
