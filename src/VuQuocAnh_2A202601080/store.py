from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
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
            import chromadb

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        embedding = self._embedding_fn(doc.content)
        metadata = dict(doc.metadata)
        if "doc_id" not in metadata:
            if "::chunk_" in doc.id:
                metadata["doc_id"] = doc.id.split("::chunk_")[0]
            else:
                metadata["doc_id"] = doc.id
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": embedding
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records:
            return []
        query_emb = self._embedding_fn(query)
        from .chunking import compute_similarity
        
        scored = []
        for r in records:
            score = compute_similarity(query_emb, r["embedding"])
            scored.append({
                "id": r["id"],
                "content": r["content"],
                "metadata": r["metadata"],
                "score": score
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        records = [self._make_record(doc) for doc in docs]
        self._store.extend(records)
        
        if self._use_chroma and self._collection:
            try:
                ids = [r["id"] for r in records]
                documents = [r["content"] for r in records]
                embeddings = [r["embedding"] for r in records]
                metadatas = [r["metadata"] for r in records]
                self._collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
            except Exception:
                pass

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection:
            return self.search_with_filter(query, top_k=top_k, metadata_filter=None)
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection:
            try:
                return self._collection.count()
            except Exception:
                pass
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if self._use_chroma and self._collection:
            query_emb = self._embedding_fn(query)
            try:
                kwargs = {
                    "query_embeddings": [query_emb],
                    "n_results": top_k
                }
                if metadata_filter:
                    kwargs["where"] = metadata_filter
                
                res = self._collection.query(**kwargs)
                results = []
                if res and res.get("documents"):
                    docs = res["documents"][0]
                    ids = res["ids"][0]
                    metadatas = res["metadatas"][0] if res.get("metadatas") else [{}] * len(docs)
                    
                    from .chunking import compute_similarity
                    for i in range(len(docs)):
                        doc_emb = self._embedding_fn(docs[i])
                        score = compute_similarity(query_emb, doc_emb)
                        results.append({
                            "id": ids[i],
                            "content": docs[i],
                            "metadata": metadatas[i],
                            "score": score
                        })
                    results.sort(key=lambda x: x["score"], reverse=True)
                return results
            except Exception:
                pass
                
        # In-memory fallback or default
        if not metadata_filter:
            return self._search_records(query, self._store, top_k)
            
        filtered_records = []
        for r in self._store:
            match = True
            for k, v in metadata_filter.items():
                if r["metadata"].get(k) != v:
                    match = False
                    break
            if match:
                filtered_records.append(r)
                
        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection:
            try:
                res_meta = self._collection.get(where={"doc_id": doc_id})
                ids_to_delete = set(res_meta.get("ids", []))
                
                res_id = self._collection.get(ids=[doc_id])
                if res_id and res_id.get("ids"):
                    ids_to_delete.update(res_id["ids"])
                
                if ids_to_delete:
                    self._collection.delete(ids=list(ids_to_delete))
                    return True
                return False
            except Exception:
                pass
                
        # In-memory
        before_len = len(self._store)
        self._store = [r for r in self._store if r["metadata"].get("doc_id") != doc_id and r["id"] != doc_id]
        after_len = len(self._store)
        return after_len < before_len
