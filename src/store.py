from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot, compute_similarity
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
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

            # TODO: initialize chromadb client + collection
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # TODO: build a normalized stored record for one document
        embedding = self._embedding_fn(doc.content)
        
        # Copy metadata và bảo đảm có doc_id
        meta_copy = dict(doc.metadata)  # Copy dict
        if 'doc_id' not in meta_copy:
            # Lấy doc_id từ phần trước dấu # (nếu có)
            # Ví dụ: "file.md#0" → "file.md"
            meta_copy['doc_id'] = doc.id.split('#')[0] if '#' in doc.id else doc.id
        
        return {
            'id': doc.id,
            'content': doc.content,
            'embedding': embedding,
            'metadata': meta_copy
        }
    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        # TODO: run in-memory similarity search over provided records
        if not records:
            return []
        
        # Embed query
        query_embedding = self._embedding_fn(query)
        
        # Tính similarity với mỗi record
        scores = []
        for record in records:
            sim = compute_similarity(
                query_embedding,
                record['embedding']
            )
            scores.append((record, sim))
        
        # Sort theo score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Trả top-k, bỏ embedding để output sạch
        results = []
        for record, score in scores[:top_k]:
            results.append({
                'id': record['id'],
                'content': record['content'],
                'score': score,
                'metadata': record['metadata']
                # Không include embedding
            })
        
        return results

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        # TODO: embed each doc and add to store
        if not docs:
            return
    
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)
            self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        # TODO: embed query, compute similarities, return top_k
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        # TODO
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        # TODO: filter by metadata, then search among filtered chunks
        
        # Nếu không có filter → search toàn bộ store
        if metadata_filter is None:
            return self._search_records(query, self._store, top_k)
        
        # Filter trước
        filtered = []
        for record in self._store:
            matches = True
            # Check từng key-value trong filter
            for key, value in metadata_filter.items():
                if record['metadata'].get(key) != value:
                    matches = False
                    break
            if matches:
                filtered.append(record)
        
        # Search trong filtered records
        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        # TODO: remove all stored chunks where metadata['doc_id'] == doc_id
        before_count = len(self._store)
        
        # Giữ lại chỉ những record có doc_id khác
        self._store = [
            r for r in self._store
            if r['metadata'].get('doc_id') != doc_id
        ]
        
        # Trả True nếu có xóa được gì
        return len(self._store) < before_count