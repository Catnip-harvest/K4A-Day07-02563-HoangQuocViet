from __future__ import annotations

import os
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.

    How the two backends relate: the in-memory list is always the source of
    truth for counting, ranking and filtering, and ChromaDB - when it is
    installed - is written to as well so the collection persists. Ranking stays
    in Python on purpose. Chroma's default index measures L2 distance, not
    cosine similarity, so letting it order the results would change the scores
    depending on whether an optional package happens to be installed. Keeping
    one scorer keeps a benchmark run reproducible on any machine in the class.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            persist_dir = os.getenv("CHROMA_PERSIST_DIR", "").strip()
            if persist_dir:
                client = chromadb.PersistentClient(path=persist_dir)
            else:
                client = chromadb.EphemeralClient()
            self._collection = client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._hydrate_from_chroma()
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _hydrate_from_chroma(self) -> None:
        """Read a persisted collection back in, so size and search agree with it."""
        existing = self._collection.get(include=["documents", "metadatas", "embeddings"])
        ids = existing.get("ids") or []
        for position, chunk_id in enumerate(ids):
            self._store.append(
                {
                    "chunk_id": chunk_id,
                    "id": (existing["metadatas"][position] or {}).get("doc_id", chunk_id),
                    "content": existing["documents"][position],
                    "metadata": dict(existing["metadatas"][position] or {}),
                    "embedding": list(existing["embeddings"][position]),
                }
            )
        self._next_index = len(self._store)

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # doc_id is what delete_document and the metadata filters key off, so it
        # is written in here once rather than trusted to every caller.
        metadata = dict(doc.metadata or {})
        metadata.setdefault("doc_id", doc.id)

        record = {
            "chunk_id": f"{doc.id}#{self._next_index}",
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records or top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        # The embedders return unit vectors, so the dot product IS the cosine
        # similarity - the division by the two magnitudes would be a division
        # by 1. compute_similarity() is the general form of the same thing.
        scored = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": _dot(query_embedding, record["embedding"]),
            }
            for record in records
        ]
        scored.sort(key=lambda result: result["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]
        self._store.extend(records)

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[record["chunk_id"] for record in records],
                    documents=[record["content"] for record in records],
                    embeddings=[record["embedding"] for record in records],
                    metadatas=[record["metadata"] for record in records],
                )
            except Exception:
                # Persistence is a convenience. Losing it must not lose the data.
                self._use_chroma = False

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            candidates = self._store
        else:
            # Filter first, then score. Scoring first and filtering afterwards
            # would spend the top_k budget on chunks that are then thrown away,
            # and a query like "student fees" would come back short.
            candidates = [
                record
                for record in self._store
                if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
            ]

        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        removed = [record for record in self._store if record["metadata"].get("doc_id") == doc_id]
        if not removed:
            return False

        self._store = [record for record in self._store if record["metadata"].get("doc_id") != doc_id]

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(ids=[record["chunk_id"] for record in removed])
            except Exception:
                self._use_chroma = False

        return True
