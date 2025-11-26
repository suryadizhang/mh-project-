"""
Knowledge Base service for semantic search and embeddings
Uses sentence-transformers for embeddings and FAISS for similarity search
"""

from datetime import datetime, timezone
import json
import os
from typing import Any
from uuid import UUID

from api.ai.endpoints.models import KnowledgeBaseChunk
from api.ai.endpoints.schemas import KBSearchRequest
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class KnowledgeBaseService:
    """Service for managing knowledge base with semantic search"""

    def __init__(self):
        # Initialize sentence transformer model
        self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2

        # FAISS index for similarity search
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product (cosine similarity)
        self.chunk_ids = []  # Maps FAISS index to UUID

        # Load index if it exists
        self._load_index()

    def _get_index_path(self) -> str:
        """Get the path for FAISS index storage"""
        return os.path.join(os.path.dirname(__file__), "..", "..", "data", "faiss_index.bin")

    def _get_ids_path(self) -> str:
        """Get the path for chunk IDs storage"""
        return os.path.join(os.path.dirname(__file__), "..", "..", "data", "chunk_ids.json")

    def _load_index(self):
        """Load FAISS index and chunk IDs from disk"""
        index_path = self._get_index_path()
        ids_path = self._get_ids_path()

        try:
            if os.path.exists(index_path) and os.path.exists(ids_path):
                self.index = faiss.read_index(index_path)
                with open(ids_path) as f:
                    self.chunk_ids = json.load(f)
        except Exception:
            # Reset index if corrupted
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.chunk_ids = []

    def _save_index(self):
        """Save FAISS index and chunk IDs to disk"""
        os.makedirs(os.path.dirname(self._get_index_path()), exist_ok=True)

        try:
            faiss.write_index(self.index, self._get_index_path())
            with open(self._get_ids_path(), "w") as f:
                json.dump(self.chunk_ids, f)
        except Exception:
            pass

    def encode_text(self, text: str) -> np.ndarray:
        """Encode text into embeddings"""
        return self.encoder.encode([text])[0]

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        """Encode multiple texts into embeddings"""
        return self.encoder.encode(texts)

    async def add_chunk(self, db: AsyncSession, chunk: KnowledgeBaseChunk) -> bool:
        """Add a new knowledge base chunk with embeddings"""
        try:
            # Generate embedding
            embedding = self.encode_text(chunk.text)

            # Store embedding in chunk (as JSON for now, will be VECTOR in production)
            chunk.vector = embedding.tolist()

            # Add to database
            db.add(chunk)
            await db.commit()

            # Add to FAISS index
            self.index.add(embedding.reshape(1, -1))
            self.chunk_ids.append(str(chunk.id))

            # Save index
            self._save_index()

            return True
        except Exception:
            await db.rollback()
            return False

    async def search_chunks(
        self, db: AsyncSession, request: KBSearchRequest
    ) -> tuple[list[dict[str, Any]], int]:
        """Search knowledge base chunks by semantic similarity"""
        try:
            start_time = datetime.now(timezone.utc)

            # Generate query embedding
            query_embedding = self.encode_text(request.query)

            # Search FAISS index
            scores, indices = self.index.search(
                query_embedding.reshape(1, -1),
                min(request.limit * 2, len(self.chunk_ids)),  # Get more results for filtering
            )

            # Filter by minimum score
            valid_results = []
            for score, idx in zip(scores[0], indices[0], strict=False):
                if idx >= 0 and score >= request.min_score:
                    chunk_id = self.chunk_ids[idx]
                    valid_results.append((chunk_id, float(score)))

            # Fetch chunk details from database
            chunk_ids = [UUID(chunk_id) for chunk_id, _ in valid_results[: request.limit]]

            query = select(KnowledgeBaseChunk).where(KnowledgeBaseChunk.id.in_(chunk_ids))
            if request.category:
                query = query.where(KnowledgeBaseChunk.category == request.category)

            result = await db.execute(query)
            chunks = result.scalars().all()

            # Create response with scores
            chunk_dict = {str(chunk.id): chunk for chunk in chunks}
            response_chunks = []

            for chunk_id, score in valid_results[: request.limit]:
                if chunk_id in chunk_dict:
                    chunk = chunk_dict[chunk_id]
                    response_chunks.append(
                        {
                            "id": str(chunk.id),
                            "title": chunk.title,
                            "text": chunk.text,
                            "category": chunk.category,
                            "tags": chunk.tags,
                            "score": score,
                            "usage_count": chunk.usage_count,
                            "success_rate": chunk.success_rate,
                        }
                    )

            # Update usage counts
            if chunk_ids:
                await db.execute(
                    update(KnowledgeBaseChunk)
                    .where(KnowledgeBaseChunk.id.in_(chunk_ids))
                    .values(usage_count=KnowledgeBaseChunk.usage_count + 1)
                )
                await db.commit()

            query_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            return response_chunks, query_time_ms

        except Exception:
            return [], 0

    async def rebuild_index(self, db: AsyncSession) -> bool:
        """Rebuild FAISS index from database"""
        try:
            # Clear current index
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.chunk_ids = []

            # Fetch all chunks
            query = select(KnowledgeBaseChunk)
            result = await db.execute(query)
            chunks = result.scalars().all()

            if not chunks:
                return True

            # Extract texts and generate embeddings
            texts = [chunk.text for chunk in chunks]
            embeddings = self.encode_batch(texts)

            # Add to FAISS index
            self.index.add(embeddings)
            self.chunk_ids = [str(chunk.id) for chunk in chunks]

            # Update database with embeddings
            for chunk, embedding in zip(chunks, embeddings, strict=False):
                chunk.vector = embedding.tolist()

            await db.commit()

            # Save index
            self._save_index()

            return True

        except Exception:
            return False

    def get_similar_chunks_text(self, query: str, limit: int = 3) -> list[str]:
        """Get similar chunks as text (for prompt context)"""
        try:
            if self.index.ntotal == 0:
                return []

            query_embedding = self.encode_text(query)
            scores, indices = self.index.search(
                query_embedding.reshape(1, -1), min(limit, len(self.chunk_ids))
            )

            # For now, return placeholder text since we need database access
            # This method will be enhanced to work with cached chunk text
            return [
                f"Similar content found (score: {score:.3f})" for score in scores[0] if score > 0.5
            ]

        except Exception:
            return []


# Global instance
kb_service = KnowledgeBaseService()
