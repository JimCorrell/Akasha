import chromadb

from .config import settings

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        settings.chroma_path.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(settings.chroma_path))
        _collection = _client.get_or_create_collection(
            name="notes",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def upsert(note_id: str, embedding: list[float], metadata: dict, snippet: str):
    _get_collection().upsert(
        ids=[note_id],
        embeddings=[embedding],
        metadatas=[metadata],
        documents=[snippet],
    )


def delete(note_id: str):
    try:
        _get_collection().delete(ids=[note_id])
    except Exception:
        pass


def search(query_embedding: list[float], limit: int = 5, threshold: float = 0.0) -> list[dict]:
    col = _get_collection()
    total = col.count()
    if total == 0:
        return []

    results = col.query(
        query_embeddings=[query_embedding],
        n_results=min(limit, total),
        include=["metadatas", "documents", "distances"],
    )

    output = []
    for i in range(len(results["ids"][0])):
        score = 1.0 - results["distances"][0][i]  # cosine distance → similarity
        if score >= threshold:
            output.append(
                {
                    "score": score,
                    "metadata": results["metadatas"][0][i],
                    "snippet": results["documents"][0][i],
                }
            )
    return output


def count() -> int:
    return _get_collection().count()
