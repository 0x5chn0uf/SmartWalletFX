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

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv(
            "SERENA_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self._model: "Optional[sentence_transformers.SentenceTransformer]" = None
        self._loading_thread: Optional[threading.Thread] = None
        self.embedding_dim = 384  # Default for MiniLM

    # ------------------------------------------------------------------
    # Lazy load
    # ------------------------------------------------------------------
    @property
    def model(self):  # noqa: D401
        if os.getenv("SERENA_DISABLE_EMBEDDINGS", "0") in {"1", "true", "yes"}:
            logger.warning("Embeddings disabled via SERENA_DISABLE_EMBEDDINGS")
            return None

        if self._model is None:
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

            logger.info("Loading embedding model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
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
            return [0.0] * self.embedding_dim
        try:
            return self.model.encode(text, convert_to_numpy=True).tolist()  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            logger.error("Embedding generation failed: %s", exc)
            return [0.0] * self.embedding_dim

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self.model is None:
            return [[0.0] * self.embedding_dim for _ in texts]
        try:
            vecs = self.model.encode(texts, convert_to_numpy=True, batch_size=32)  # type: ignore[attr-defined]
            return vecs.tolist()
        except Exception as exc:
            logger.error("Batch embedding generation failed: %s", exc)
            return [[0.0] * self.embedding_dim for _ in texts]


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
            return 0.0
        return float(np.dot(a, b) / (n1 * n2))
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
            return [0.0] * len(vectors)
        q /= qn
        norms = np.linalg.norm(mat, axis=1)
        norms[norms == 0] = 1
        mat = mat / norms[:, np.newaxis]
        return np.dot(mat, q).tolist()
    except Exception as exc:
        logger.error("Batch cosine similarity error: %s", exc)
        return [0.0] * len(vectors)


@lru_cache(maxsize=1)
def get_default_generator() -> EmbeddingGenerator:
    return EmbeddingGenerator()


@lru_cache(maxsize=1024)
def generate_embedding(text: str) -> List[float]:
    return get_default_generator().generate_embedding(text)
