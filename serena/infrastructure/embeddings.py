"""Embedding generation and utilities.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
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
        logger.info("EmbeddingGenerator initialized with device: %s", self._device)

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
